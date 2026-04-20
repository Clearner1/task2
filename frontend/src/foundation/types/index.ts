/** Task status enum — mirrors backend contract exactly */
export const TaskStatus = {
  IMPORTED: 'IMPORTED',
  PREPROCESSED: 'PREPROCESSED',
  READY: 'READY',
  IN_PROGRESS: 'IN_PROGRESS',
  SUBMITTED: 'SUBMITTED',
  REVIEWED: 'REVIEWED',
  EXPORTED: 'EXPORTED',
} as const;

export type TaskStatusType = (typeof TaskStatus)[keyof typeof TaskStatus];

/** Badge-friendly key mapping */
export function statusToBadgeKey(
  s: TaskStatusType,
): 'imported' | 'preprocessed' | 'ready' | 'in-progress' | 'submitted' | 'reviewed' | 'exported' {
  const map: Record<TaskStatusType, ReturnType<typeof statusToBadgeKey>> = {
    IMPORTED: 'imported',
    PREPROCESSED: 'preprocessed',
    READY: 'ready',
    IN_PROGRESS: 'in-progress',
    SUBMITTED: 'submitted',
    REVIEWED: 'reviewed',
    EXPORTED: 'exported',
  };
  return map[s];
}

/* ========== Backend-aligned types ========== */

/** MediaItem from GET /api/media and GET /api/media/{id} */
export interface MediaRecord {
  media_id: string;
  source_path: string;
  media_type: string;
  detected_format: string | null;
  duration_ms: number | null;
  status: TaskStatusType;
  failure_reason: string | null;
  stream_url: string;
  created_at: string;
  updated_at: string;
}

/** TaskItem from GET /api/tasks list */
export interface TaskItem {
  task_id: string;
  media_id: string;
  status: TaskStatusType;
  assigned_to: string | null;
  lock_owner: string | null;
  lock_expires_at: string | null;
  submitted_at: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

/** AnnotationPayload — shared between autosave, submit, and display */
export interface AnnotationPayload {
  primary_emotion: string;
  secondary_emotions: string[];
  intensity: number;
  confidence: number;
  valence: number | null;
  arousal: number | null;
  notes: string;
}

/** AnnotationView from backend */
export interface AnnotationView {
  annotation_id: string;
  task_id: string;
  media_id: string;
  annotator_id: string;
  annotation: AnnotationPayload;
  is_draft: boolean;
  version: number;
  created_at: string;
  updated_at: string;
}

/** TaskDetail from GET /api/tasks/{id} and GET /api/tasks/next */
export interface TaskDetail {
  task: TaskItem;
  media: MediaRecord;
  latest_draft: AnnotationView | null;
  latest_annotation: AnnotationView | null;
}

/** Flattened task for UI consumption (used by domain hooks) */
export interface AnnotationTask {
  task_id: string;
  media_id: string;
  status: TaskStatusType;
  assigned_to: string | null;
  locked_until: string | null;
  created_at: string;
  updated_at: string;
  media?: MediaRecord;
  draft?: AnnotationPayload | null;
}

/** Convert backend TaskDetail to flat AnnotationTask for UI */
export function flattenTaskDetail(detail: TaskDetail): AnnotationTask {
  return {
    task_id: detail.task.task_id,
    media_id: detail.task.media_id,
    status: detail.task.status,
    assigned_to: detail.task.assigned_to,
    locked_until: detail.task.lock_expires_at,
    created_at: detail.task.created_at,
    updated_at: detail.task.updated_at,
    media: detail.media,
    draft: detail.latest_annotation?.annotation ?? detail.latest_draft?.annotation ?? null,
  };
}

/** ReviewDecision — maps to backend ReviewRequest/ReviewResponse */
export interface ReviewDecision {
  task_id: string;
  decision: 'approved' | 'rejected';
  reviewer_id: string;
  reviewed_at: string;
}

/** ExportBatch — maps to backend ExportResponse */
export interface ExportBatch {
  batch_id: string;
  status: string;
  formats: string[];
  output_paths: string[];
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ApiError {
  code: string;
  message: string;
  entity_id?: string;
  retryable: boolean;
}

/** Default blank annotation payload */
export function createBlankAnnotation(): AnnotationPayload {
  return {
    primary_emotion: '',
    secondary_emotions: [],
    intensity: 3,
    confidence: 3,
    valence: 0,
    arousal: 3,
    notes: '',
  };
}

/** Primary emotion options from config.md default */
export const PRIMARY_EMOTIONS = [
  { value: 'neutral', label: 'Neutral' },
  { value: 'happy', label: 'Happy' },
  { value: 'sad', label: 'Sad' },
  { value: 'angry', label: 'Angry' },
  { value: 'fear', label: 'Fear' },
  { value: 'surprise', label: 'Surprise' },
  { value: 'disgust', label: 'Disgust' },
  { value: 'other', label: 'Other' },
] as const;
