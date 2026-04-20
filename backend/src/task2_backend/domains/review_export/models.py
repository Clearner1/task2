from dataclasses import dataclass


@dataclass(frozen=True)
class ExportBatchRecord:
    batch_id: str
    status: str
    formats: str
    output_paths: str
    created_at: str
