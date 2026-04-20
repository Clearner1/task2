from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from threading import Event, Lock, Thread
from typing import Any, Callable

from task2_backend.common.enums import JobFailureStatus, MaintenanceRunStatus, TaskStatus
from task2_backend.common.exceptions import Task2Error
from task2_backend.common.time import isoformat, now_utc
from task2_backend.foundation.config import RetryConfig
from task2_backend.foundation.database import Database

logger = logging.getLogger(__name__)

ReplayHandler = Callable[["JobFailureRecord"], None]
ReclaimExpiredLocksHandler = Callable[[], int]


@dataclass(frozen=True)
class JobFailureRecord:
    id: int
    job_name: str
    entity_id: str | None
    failure_code: str
    message: str
    retry_count: int
    max_attempts: int
    status: JobFailureStatus
    next_retry_at: str | None
    payload: dict[str, Any]
    created_at: str
    updated_at: str
    resolved_at: str | None


@dataclass(frozen=True)
class MaintenanceRunRecord:
    id: int
    status: MaintenanceRunStatus
    started_at: str
    finished_at: str | None
    summary: dict[str, Any]
    error_message: str | None


@dataclass(frozen=True)
class OpsStatusSnapshot:
    media_status_counts: dict[str, int]
    task_status_counts: dict[str, int]
    pending_retry_jobs: int
    terminal_failure_jobs: int
    stale_lock_count: int
    last_maintenance_run: MaintenanceRunRecord | None


class OperationsService:
    def __init__(self, database: Database, retry_config: RetryConfig):
        self.database = database
        self.retry_config = retry_config

    def record_job_failure(
        self,
        job_name: str,
        entity_id: str | None,
        exc: Exception,
        *,
        payload: dict[str, Any] | None = None,
        occurred_at: str | None = None,
    ) -> None:
        timestamp = occurred_at or isoformat(now_utc())
        retryable = isinstance(exc, Task2Error) and exc.retryable
        failure_code = exc.code if isinstance(exc, Task2Error) else exc.__class__.__name__
        message = exc.message if isinstance(exc, Task2Error) else str(exc)
        status = JobFailureStatus.PENDING if retryable else JobFailureStatus.TERMINAL
        next_retry_at = self._compute_next_retry_at(timestamp, 0) if retryable else None
        payload_json = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True)

        with self.database.connect() as connection:
            existing = self._find_pending_failure(connection, job_name, entity_id)
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO job_failures (
                        job_name, entity_id, failure_code, message, retry_count, max_attempts,
                        status, next_retry_at, payload_json, updated_at, resolved_at, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        job_name,
                        entity_id,
                        failure_code,
                        message,
                        0,
                        self.retry_config.max_attempts,
                        status.value,
                        next_retry_at,
                        payload_json,
                        timestamp,
                        None,
                        timestamp,
                    ],
                )
                return

            connection.execute(
                """
                UPDATE job_failures
                SET failure_code = ?, message = ?, status = ?, next_retry_at = ?, payload_json = ?, updated_at = ?, resolved_at = NULL
                WHERE id = ?
                """,
                [
                    failure_code,
                    message,
                    status.value,
                    next_retry_at,
                    payload_json,
                    timestamp,
                    existing["id"],
                ],
            )

    def resolve_job_failure(self, job_name: str, entity_id: str | None, *, resolved_at: str | None = None) -> None:
        timestamp = resolved_at or isoformat(now_utc())
        with self.database.connect() as connection:
            existing = self._find_pending_failure(connection, job_name, entity_id)
            if existing is None:
                return
            connection.execute(
                """
                UPDATE job_failures
                SET status = ?, resolved_at = ?, updated_at = ?, next_retry_at = NULL
                WHERE id = ?
                """,
                [JobFailureStatus.RESOLVED.value, timestamp, timestamp, existing["id"]],
            )

    def list_due_job_failures(self, now_iso: str, limit: int) -> list[JobFailureRecord]:
        with self.database.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM job_failures
                WHERE status = ? AND next_retry_at IS NOT NULL AND next_retry_at <= ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                [JobFailureStatus.PENDING.value, now_iso, limit],
            ).fetchall()
        return [self._job_failure_from_row(row) for row in rows]

    def handle_replay_failure(self, record: JobFailureRecord, exc: Exception, *, occurred_at: str | None = None) -> JobFailureStatus:
        timestamp = occurred_at or isoformat(now_utc())
        retryable = isinstance(exc, Task2Error) and exc.retryable
        failure_code = exc.code if isinstance(exc, Task2Error) else exc.__class__.__name__
        message = exc.message if isinstance(exc, Task2Error) else str(exc)
        retry_count = record.retry_count + 1

        if not retryable or retry_count >= record.max_attempts:
            next_status = JobFailureStatus.TERMINAL
            next_retry_at = None
            resolved_at = timestamp
        else:
            next_status = JobFailureStatus.PENDING
            next_retry_at = self._compute_next_retry_at(timestamp, retry_count)
            resolved_at = None

        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE job_failures
                SET failure_code = ?, message = ?, retry_count = ?, status = ?, next_retry_at = ?, updated_at = ?, resolved_at = ?
                WHERE id = ?
                """,
                [
                    failure_code,
                    message,
                    retry_count,
                    next_status.value,
                    next_retry_at,
                    timestamp,
                    resolved_at,
                    record.id,
                ],
            )
        return next_status

    def mark_job_failure_terminal(
        self,
        failure_id: int,
        *,
        failure_code: str,
        message: str,
        occurred_at: str | None = None,
    ) -> None:
        timestamp = occurred_at or isoformat(now_utc())
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE job_failures
                SET failure_code = ?, message = ?, status = ?, next_retry_at = NULL, updated_at = ?, resolved_at = ?
                WHERE id = ?
                """,
                [failure_code, message, JobFailureStatus.TERMINAL.value, timestamp, timestamp, failure_id],
            )

    def start_maintenance_run(self, started_at: str | None = None) -> int:
        timestamp = started_at or isoformat(now_utc())
        with self.database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO maintenance_runs (status, started_at, finished_at, summary_json, error_message)
                VALUES (?, ?, ?, ?, ?)
                """,
                [MaintenanceRunStatus.RUNNING.value, timestamp, None, "{}", None],
            )
            return int(cursor.lastrowid)

    def finish_maintenance_run(
        self,
        run_id: int,
        *,
        status: MaintenanceRunStatus,
        summary: dict[str, Any],
        finished_at: str | None = None,
        error_message: str | None = None,
    ) -> None:
        timestamp = finished_at or isoformat(now_utc())
        with self.database.connect() as connection:
            connection.execute(
                """
                UPDATE maintenance_runs
                SET status = ?, finished_at = ?, summary_json = ?, error_message = ?
                WHERE id = ?
                """,
                [status.value, timestamp, json.dumps(summary, ensure_ascii=False, sort_keys=True), error_message, run_id],
            )

    def get_status_snapshot(self, now_iso: str | None = None) -> OpsStatusSnapshot:
        timestamp = now_iso or isoformat(now_utc())
        with self.database.connect() as connection:
            media_rows = connection.execute(
                "SELECT status, COUNT(*) AS count FROM media_files GROUP BY status"
            ).fetchall()
            task_rows = connection.execute(
                "SELECT status, COUNT(*) AS count FROM annotation_tasks GROUP BY status"
            ).fetchall()
            pending_retry_jobs = int(
                connection.execute(
                    "SELECT COUNT(*) AS count FROM job_failures WHERE status = ?",
                    [JobFailureStatus.PENDING.value],
                ).fetchone()["count"]
            )
            terminal_failure_jobs = int(
                connection.execute(
                    "SELECT COUNT(*) AS count FROM job_failures WHERE status = ?",
                    [JobFailureStatus.TERMINAL.value],
                ).fetchone()["count"]
            )
            stale_lock_count = int(
                connection.execute(
                    """
                    SELECT COUNT(*) AS count
                    FROM annotation_tasks
                    WHERE status = ? AND lock_expires_at IS NOT NULL AND lock_expires_at < ?
                    """,
                    [TaskStatus.IN_PROGRESS.value, timestamp],
                ).fetchone()["count"]
            )
            maintenance_row = connection.execute(
                "SELECT * FROM maintenance_runs ORDER BY id DESC LIMIT 1"
            ).fetchone()

        media_status_counts = {status.value: 0 for status in TaskStatus}
        task_status_counts = {status.value: 0 for status in TaskStatus}
        for row in media_rows:
            media_status_counts[row["status"]] = int(row["count"])
        for row in task_rows:
            task_status_counts[row["status"]] = int(row["count"])

        last_maintenance_run = self._maintenance_run_from_row(maintenance_row) if maintenance_row else None
        return OpsStatusSnapshot(
            media_status_counts=media_status_counts,
            task_status_counts=task_status_counts,
            pending_retry_jobs=pending_retry_jobs,
            terminal_failure_jobs=terminal_failure_jobs,
            stale_lock_count=stale_lock_count,
            last_maintenance_run=last_maintenance_run,
        )

    def _compute_next_retry_at(self, now_iso: str, retry_count: int) -> str:
        base = datetime.fromisoformat(now_iso)
        delay = min(
            self.retry_config.base_delay_seconds * (2 ** retry_count),
            self.retry_config.max_delay_seconds,
        )
        return isoformat(base + timedelta(seconds=delay))

    @staticmethod
    def _payload_from_json(value: str | None) -> dict[str, Any]:
        if not value:
            return {}
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}

    @staticmethod
    def _maintenance_run_from_row(row) -> MaintenanceRunRecord:
        summary = OperationsService._payload_from_json(row["summary_json"])
        return MaintenanceRunRecord(
            id=int(row["id"]),
            status=MaintenanceRunStatus(row["status"]),
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            summary=summary,
            error_message=row["error_message"],
        )

    @staticmethod
    def _job_failure_from_row(row) -> JobFailureRecord:
        return JobFailureRecord(
            id=int(row["id"]),
            job_name=row["job_name"],
            entity_id=row["entity_id"],
            failure_code=row["failure_code"],
            message=row["message"],
            retry_count=int(row["retry_count"]),
            max_attempts=int(row["max_attempts"]),
            status=JobFailureStatus(row["status"]),
            next_retry_at=row["next_retry_at"],
            payload=OperationsService._payload_from_json(row["payload_json"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            resolved_at=row["resolved_at"],
        )

    @staticmethod
    def _find_pending_failure(connection, job_name: str, entity_id: str | None):
        if entity_id is None:
            return connection.execute(
                """
                SELECT id FROM job_failures
                WHERE job_name = ? AND entity_id IS NULL AND status = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                [job_name, JobFailureStatus.PENDING.value],
            ).fetchone()
        return connection.execute(
            """
            SELECT id FROM job_failures
            WHERE job_name = ? AND entity_id = ? AND status = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            [job_name, entity_id, JobFailureStatus.PENDING.value],
        ).fetchone()


class MaintenanceRunner:
    def __init__(
        self,
        *,
        interval_seconds: int,
        shutdown_grace_seconds: int,
        replay_limit: int,
        operations_service: OperationsService,
        reclaim_expired_locks: ReclaimExpiredLocksHandler,
        replay_handlers: dict[str, ReplayHandler],
    ):
        self.interval_seconds = interval_seconds
        self.shutdown_grace_seconds = shutdown_grace_seconds
        self.replay_limit = replay_limit
        self.operations_service = operations_service
        self.reclaim_expired_locks = reclaim_expired_locks
        self.replay_handlers = replay_handlers
        self._stop_event = Event()
        self._run_lock = Lock()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run_forever, name="task2-maintenance", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is None:
            return
        self._thread.join(timeout=self.shutdown_grace_seconds)

    def run_once(self) -> dict[str, int]:
        if not self._run_lock.acquire(blocking=False):
            return {
                "reclaimed_expired_locks": 0,
                "due_retry_jobs": 0,
                "resolved_retry_jobs": 0,
                "terminal_retry_jobs": 0,
            }

        run_id = self.operations_service.start_maintenance_run()
        summary = {
            "reclaimed_expired_locks": 0,
            "due_retry_jobs": 0,
            "resolved_retry_jobs": 0,
            "terminal_retry_jobs": 0,
        }

        try:
            summary["reclaimed_expired_locks"] = self.reclaim_expired_locks()
            due_jobs = self.operations_service.list_due_job_failures(isoformat(now_utc()), self.replay_limit)
            summary["due_retry_jobs"] = len(due_jobs)

            for record in due_jobs:
                handler = self.replay_handlers.get(record.job_name)
                if handler is None:
                    self.operations_service.mark_job_failure_terminal(
                        record.id,
                        failure_code="missing_replay_handler",
                        message=f"No replay handler registered for {record.job_name}",
                    )
                    summary["terminal_retry_jobs"] += 1
                    continue

                try:
                    handler(record)
                except Exception as exc:
                    next_status = self.operations_service.handle_replay_failure(record, exc)
                    if next_status == JobFailureStatus.TERMINAL:
                        summary["terminal_retry_jobs"] += 1
                else:
                    self.operations_service.resolve_job_failure(record.job_name, record.entity_id)
                    summary["resolved_retry_jobs"] += 1

            self.operations_service.finish_maintenance_run(
                run_id,
                status=MaintenanceRunStatus.SUCCESS,
                summary=summary,
            )
            return summary
        except Exception as exc:
            self.operations_service.finish_maintenance_run(
                run_id,
                status=MaintenanceRunStatus.FAILED,
                summary=summary,
                error_message=str(exc),
            )
            logger.exception("Maintenance cycle failed.")
            raise
        finally:
            self._run_lock.release()

    def _run_forever(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                logger.exception("Maintenance runner iteration crashed.")
            if self._stop_event.wait(self.interval_seconds):
                return
