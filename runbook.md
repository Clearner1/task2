# Task2 Runbook

## Operational Goal

The system must run without manual intervention for at least 24 hours while maintaining correct state, retry behavior, and recoverability.

## Core Operational Loop

1. scan configured input directories
2. register new media idempotently
3. preprocess media, generate normalized assets, and persist results
4. expose ready tasks to annotators
5. heartbeat active task leases and autosave dirty annotations
6. review completed annotations
7. export reviewed results
8. monitor logs, failures, and stale locks

The unattended runtime depends on a background maintenance loop. When `runtime.worker_enabled=true`, the backend starts a maintenance runner that wakes up every `runtime.maintenance_interval_seconds`.

## Stability Requirements

- every background action writes durable state before acknowledging completion
- every retryable failure increments a persisted retry counter
- every terminal failure writes a durable error record
- every long-running step logs start, success, retry, and failure events
- normalized asset generation writes deterministic output paths under the media workspace

## Retry Handling

- retryable failures use the centralized retry helper in `foundation`
- retries are exponential with capped delay
- terminal failures move the record into an explicit failed state or failure log table
- operations must never spin indefinitely

## Recovery Procedures

### Service Restart

- reload configuration
- reopen database
- scan for unfinished background jobs from durable failure records
- reclaim expired task locks
- resume retryable jobs that have not exceeded max attempts

### Maintenance Cycle

Each cycle must do the following in order:

1. record a maintenance-run start row
2. reclaim expired task locks
3. load due retryable jobs
4. replay each supported job through its registered handler
5. resolve successful jobs or advance retry counters for failed jobs
6. record the final maintenance-run result

### Stale Task Locks

- detect locks whose expiry is in the past
- mark them as abandoned
- either return them to `READY` or place them in a recovery queue according to policy
- write an audit event

### Active Task Lease

- active workbenches send periodic heartbeat requests to extend task leases
- autosave is for draft persistence and also refreshes the active lease when draft data changes
- explicit release is required when users skip a task, navigate away, or abandon the current workbench

### Export Recovery

- if an export batch is partially written, the batch record remains non-final
- rerun only unfinished outputs
- finalized outputs must be immutable and versioned

### Durable Failure Records

- retryable failures are stored with job name, entity id, retry count, next retry time, and last error details
- successful replay marks the record resolved instead of deleting operational history
- exhausted failures become terminal and remain visible to ops status endpoints
- media normalization failures replay against the same deterministic output paths instead of producing new filenames

## Minimum Observability

- structured application logs
- error logs with exception category and entity id
- counters for media by status
- counters for tasks by status
- failure counts by category
- retry counts by operation
- stale lock count
- last maintenance run status and timestamp

## Manual Checks

- verify worker queue is draining
- verify no task remains locked past timeout without heartbeat updates
- verify export batches match reviewed task counts
- verify repeated scans do not create duplicate records
