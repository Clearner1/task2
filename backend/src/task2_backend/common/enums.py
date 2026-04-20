from enum import Enum


class TaskStatus(str, Enum):
    IMPORTED = "IMPORTED"
    PREPROCESSED = "PREPROCESSED"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    REVIEWED = "REVIEWED"
    EXPORTED = "EXPORTED"


class MediaType(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"
    UNKNOWN = "unknown"


class ReviewDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class ExportStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class JobFailureStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    TERMINAL = "terminal"


class MaintenanceRunStatus(str, Enum):
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
