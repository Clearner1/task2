class Task2Error(Exception):
    code = "task2_error"
    retryable = False
    status_code = 500

    def __init__(self, message: str, *, entity_id: str | None = None):
        super().__init__(message)
        self.message = message
        self.entity_id = entity_id


class ConfigValidationError(Task2Error):
    code = "config_validation_error"
    status_code = 500


class MediaDetectionError(Task2Error):
    code = "media_detection_error"
    retryable = True
    status_code = 503


class MediaNormalizationError(Task2Error):
    code = "media_normalization_error"
    retryable = True
    status_code = 503


class UnsupportedMediaFormatError(Task2Error):
    code = "unsupported_media_format"
    status_code = 422


class DatabaseLockError(Task2Error):
    code = "database_lock_conflict"
    retryable = True
    status_code = 503


class TaskLockError(Task2Error):
    code = "task_lock_conflict"
    status_code = 409


class AnnotationValidationError(Task2Error):
    code = "annotation_validation_error"
    status_code = 400


class ExportWriteError(Task2Error):
    code = "export_write_error"
    retryable = True
    status_code = 503


class NotFoundError(Task2Error):
    code = "not_found"
    status_code = 404
