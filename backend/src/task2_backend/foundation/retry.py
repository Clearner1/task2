from __future__ import annotations

import logging
import random
import time
from typing import Callable, TypeVar

from task2_backend.common.exceptions import Task2Error
from task2_backend.foundation.config import RetryConfig

T = TypeVar("T")
logger = logging.getLogger(__name__)


def run_with_retry(
    operation_name: str,
    entity_id: str | None,
    config: RetryConfig,
    func: Callable[[], T],
) -> T:
    attempt = 0
    while True:
        attempt += 1
        try:
            return func()
        except Task2Error as exc:
            should_retry = exc.retryable and attempt < config.max_attempts
            logger.warning(
                "operation=%s entity_id=%s attempt=%s retryable=%s message=%s",
                operation_name,
                entity_id,
                attempt,
                should_retry,
                exc.message,
            )
            if not should_retry:
                raise
            delay = min(config.base_delay_seconds * (2 ** (attempt - 1)), config.max_delay_seconds)
            if config.jitter_enabled:
                delay += random.random()
            time.sleep(delay)
