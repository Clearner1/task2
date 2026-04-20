import type {
  MediaRecord,
  AnnotationTask,
  AnnotationPayload,
  ReviewDecision,
  ExportBatch,
  PaginatedResponse,
  TaskItem,
} from '../types';

/** API adapter interface — both mock and real implementations conform to this */
export interface ApiAdapter {
  // Media
  listMedia(params: { page?: number; page_size?: number; status?: string }): Promise<PaginatedResponse<MediaRecord>>;
  getMedia(mediaId: string): Promise<MediaRecord>;
  importMedia(): Promise<{ imported: number; existing: number }>;
  preprocessMedia(): Promise<{ processed: number; failed: number }>;
  getMediaStreamUrl(mediaId: string): string;

  // Tasks
  listTasks(params: { page?: number; page_size?: number; status?: string; assigned_to?: string }): Promise<PaginatedResponse<TaskItem>>;
  getNextTask(annotatorId?: string): Promise<AnnotationTask>;
  getTask(taskId: string): Promise<AnnotationTask>;
  heartbeatTask(taskId: string, annotatorId: string): Promise<void>;
  autosaveTask(taskId: string, annotatorId: string, payload: AnnotationPayload): Promise<void>;
  releaseTask(taskId: string, annotatorId: string, options?: { keepalive?: boolean; reason?: string }): Promise<void>;
  submitTask(taskId: string, annotatorId: string, payload: AnnotationPayload): Promise<void>;

  // Review & Export
  reviewTask(taskId: string, decision: { decision: 'approved' | 'rejected'; reviewer_id: string; notes?: string }): Promise<ReviewDecision>;
  exportBatch(params: { formats?: string[] }): Promise<ExportBatch>;
  getExportBatch(batchId: string): Promise<ExportBatch>;
}
