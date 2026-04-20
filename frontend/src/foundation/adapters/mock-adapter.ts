import type { ApiAdapter } from './types';
import type {
  MediaRecord,
  AnnotationTask,
  AnnotationPayload,
  PaginatedResponse,
  TaskItem,
} from '../types';
import { TaskStatus } from '../types';

/* =============== Mock Data =============== */

const MOCK_MEDIA: MediaRecord[] = [
  { media_id: '1226-141268-0001', source_path: 'task2/media/1226-141268-0001.mp3', media_type: 'audio', detected_format: 'mp3', duration_ms: 14670, status: TaskStatus.READY, failure_reason: null, stream_url: '/api/media/1226-141268-0001/stream', created_at: '2026-04-20T10:00:00+08:00', updated_at: '2026-04-20T10:05:00+08:00' },
  { media_id: '1250-135777-0085', source_path: 'task2/media/1250-135777-0085.mp3', media_type: 'audio', detected_format: 'mp3', duration_ms: 4500, status: TaskStatus.READY, failure_reason: null, stream_url: '/api/media/1250-135777-0085/stream', created_at: '2026-04-20T10:00:00+08:00', updated_at: '2026-04-20T10:05:00+08:00' },
  { media_id: '13069-13511-000007', source_path: 'task2/media/13069-13511-000007.mp3', media_type: 'audio', detected_format: 'mp3', duration_ms: 12800, status: TaskStatus.IMPORTED, failure_reason: null, stream_url: '/api/media/13069-13511-000007/stream', created_at: '2026-04-20T10:00:00+08:00', updated_at: '2026-04-20T10:00:00+08:00' },
  { media_id: '1603-141713-0017', source_path: 'task2/media/1603-141713-0017.mp3', media_type: 'audio', detected_format: 'mp3', duration_ms: 9800, status: TaskStatus.PREPROCESSED, failure_reason: null, stream_url: '/api/media/1603-141713-0017/stream', created_at: '2026-04-20T10:00:00+08:00', updated_at: '2026-04-20T10:03:00+08:00' },
  { media_id: '1756-134819-0020', source_path: 'task2/media/1756-134819-0020.mp3', media_type: 'audio', detected_format: 'mp3', duration_ms: 16700, status: TaskStatus.SUBMITTED, failure_reason: null, stream_url: '/api/media/1756-134819-0020/stream', created_at: '2026-04-20T10:00:00+08:00', updated_at: '2026-04-20T12:00:00+08:00' },
  { media_id: '2494-156014-0003', source_path: 'task2/media/2494-156014-0003.mp3', media_type: 'audio', detected_format: 'mp3', duration_ms: 5200, status: TaskStatus.REVIEWED, failure_reason: null, stream_url: '/api/media/2494-156014-0003/stream', created_at: '2026-04-20T10:00:00+08:00', updated_at: '2026-04-20T13:00:00+08:00' },
  { media_id: '2581-157858-0019', source_path: 'task2/media/2581-157858-0019.mp3', media_type: 'audio', detected_format: 'mp3', duration_ms: 18800, status: TaskStatus.IN_PROGRESS, failure_reason: null, stream_url: '/api/media/2581-157858-0019/stream', created_at: '2026-04-20T10:00:00+08:00', updated_at: '2026-04-20T11:30:00+08:00' },
  { media_id: '3557-8342-0007', source_path: 'task2/media/3557-8342-0007.mp3', media_type: 'audio', detected_format: 'mp3', duration_ms: 2280, status: TaskStatus.READY, failure_reason: null, stream_url: '/api/media/3557-8342-0007/stream', created_at: '2026-04-20T10:00:00+08:00', updated_at: '2026-04-20T10:05:00+08:00' },
  { media_id: '3982-178459-0065', source_path: 'task2/media/3982-178459-0065.mp3', media_type: 'audio', detected_format: 'mp3', duration_ms: 15700, status: TaskStatus.EXPORTED, failure_reason: null, stream_url: '/api/media/3982-178459-0065/stream', created_at: '2026-04-20T10:00:00+08:00', updated_at: '2026-04-20T15:00:00+08:00' },
  { media_id: '8531-282933-0044', source_path: 'task2/media/8531-282933-0044.mp3', media_type: 'audio', detected_format: 'mp3', duration_ms: 17200, status: TaskStatus.READY, failure_reason: null, stream_url: '/api/media/8531-282933-0044/stream', created_at: '2026-04-20T10:00:00+08:00', updated_at: '2026-04-20T10:05:00+08:00' },
];

let taskIdCounter = 1;
const MOCK_TASKS: (TaskItem & { _media: MediaRecord; _draft: AnnotationPayload | null })[] = MOCK_MEDIA.map((m) => ({
  task_id: `task-${String(taskIdCounter++).padStart(4, '0')}`,
  media_id: m.media_id,
  status: m.status,
  assigned_to: m.status === 'IN_PROGRESS' ? 'annotator_01' : null,
  lock_owner: m.status === 'IN_PROGRESS' ? 'annotator_01' : null,
  lock_expires_at: null,
  submitted_at: null,
  reviewed_at: null,
  created_at: m.created_at,
  updated_at: m.updated_at,
  _media: m,
  _draft: null,
}));

const MOCK_SUBMITTED_ANNOTATION: AnnotationPayload = {
  primary_emotion: 'sad',
  secondary_emotions: [],
  intensity: 3,
  confidence: 4,
  valence: -0.6,
  arousal: 2,
  notes: '语气平稳但整体偏低落',
};

/* =============== Helpers =============== */

function delay(ms = 300): Promise<void> {
  return new Promise((r) => setTimeout(r, ms + Math.random() * 200));
}

function paginate<T>(items: T[], page: number, pageSize: number): PaginatedResponse<T> {
  const start = (page - 1) * pageSize;
  return {
    items: items.slice(start, start + pageSize),
    total: items.length,
    page,
    page_size: pageSize,
  };
}

/* =============== Mock Adapter =============== */

export function createMockAdapter(): ApiAdapter {
  // mutable copy for state changes
  const media = [...MOCK_MEDIA];
  const tasks = [...MOCK_TASKS];

  return {
    async listMedia({ page = 1, page_size = 20, status }) {
      await delay();
      const filtered = status ? media.filter((m) => m.status === status) : media;
      return paginate(filtered, page, page_size);
    },

    async getMedia(mediaId) {
      await delay(150);
      const m = media.find((x) => x.media_id === mediaId);
      if (!m) throw new Error(`Media ${mediaId} not found`);
      return m;
    },

    async importMedia() {
      await delay(600);
      return { imported: media.length, existing: 0 };
    },

    async preprocessMedia() {
      await delay(800);
      let count = 0;
      media.forEach((m) => {
        if (m.status === TaskStatus.IMPORTED) {
          m.status = TaskStatus.PREPROCESSED;
          count++;
        }
      });
      tasks.forEach((t) => {
        const m = media.find((x) => x.media_id === t.media_id);
        if (m) t.status = m.status;
      });
      return { processed: count, failed: 0 };
    },

    getMediaStreamUrl(mediaId) {
      return `/api/media/${mediaId}/stream`;
    },

    async listTasks({ page = 1, page_size = 20, status, assigned_to }) {
      await delay();
      let filtered = tasks.map(({ _media, _draft, ...t }) => t);
      if (status) filtered = filtered.filter((t) => t.status === status);
      if (assigned_to) filtered = filtered.filter((t) => t.assigned_to === assigned_to);
      return paginate(filtered, page, page_size);
    },

    async getNextTask() {
      await delay(200);
      const task = tasks.find((t) => t.status === TaskStatus.READY);
      if (!task) throw new Error('No tasks available');
      task.status = TaskStatus.IN_PROGRESS;
      task.assigned_to = 'annotator_01';
      task.lock_owner = 'annotator_01';
      task.lock_expires_at = new Date(Date.now() + 300_000).toISOString();
      return {
        task_id: task.task_id,
        media_id: task.media_id,
        status: task.status,
        assigned_to: task.assigned_to,
        locked_until: task.lock_expires_at,
        created_at: task.created_at,
        updated_at: task.updated_at,
        media: task._media,
        draft: task._draft,
      } satisfies AnnotationTask;
    },

    async getTask(taskId) {
      await delay(150);
      const t = tasks.find((x) => x.task_id === taskId);
      if (!t) throw new Error(`Task ${taskId} not found`);
      return {
        task_id: t.task_id,
        media_id: t.media_id,
        status: t.status,
        assigned_to: t.assigned_to,
        locked_until: t.lock_expires_at,
        created_at: t.created_at,
        updated_at: t.updated_at,
        media: t._media,
        draft: t._draft,
      } satisfies AnnotationTask;
    },

    async heartbeatTask(taskId, annotatorId) {
      await delay(75);
      const t = tasks.find((x) => x.task_id === taskId);
      if (!t) throw new Error(`Task ${taskId} not found`);
      t.assigned_to = annotatorId;
      t.lock_owner = annotatorId;
      t.lock_expires_at = new Date(Date.now() + 300_000).toISOString();
    },

    async autosaveTask(taskId, _annotatorId, payload) {
      await delay(100);
      const t = tasks.find((x) => x.task_id === taskId);
      if (!t) throw new Error(`Task ${taskId} not found`);
      t._draft = payload;
      t.lock_expires_at = new Date(Date.now() + 300_000).toISOString();
    },

    async releaseTask(taskId) {
      await delay(75);
      const t = tasks.find((x) => x.task_id === taskId);
      if (!t) throw new Error(`Task ${taskId} not found`);
      if (t.status === TaskStatus.IN_PROGRESS) {
        t.status = TaskStatus.READY;
        t.assigned_to = null;
        t.lock_owner = null;
        t.lock_expires_at = null;
      }
    },

    async submitTask(taskId, _annotatorId, payload) {
      await delay(400);
      const t = tasks.find((x) => x.task_id === taskId);
      if (!t) throw new Error(`Task ${taskId} not found`);
      if (!payload.primary_emotion) throw new Error('primary_emotion is required');
      t.status = TaskStatus.SUBMITTED;
      t._draft = payload;
    },

    async reviewTask(taskId, decision) {
      await delay(300);
      const t = tasks.find((x) => x.task_id === taskId);
      if (!t) throw new Error(`Task ${taskId} not found`);
      t.status = TaskStatus.REVIEWED;
      return {
        task_id: taskId,
        decision: decision.decision,
        reviewer_id: decision.reviewer_id,
        reviewed_at: new Date().toISOString(),
      };
    },

    async exportBatch({ formats = ['json'] } = {}) {
      await delay(500);
      const reviewed = tasks.filter((t) => t.status === TaskStatus.REVIEWED);
      reviewed.forEach((t) => (t.status = TaskStatus.EXPORTED));
      return {
        batch_id: `batch-${Date.now()}`,
        status: 'success',
        formats,
        output_paths: formats.map((f) => `task2/exports/batch_${Date.now()}.${f}`),
        created_at: new Date().toISOString(),
      };
    },

    async getExportBatch(batchId) {
      await delay(150);
      return {
        batch_id: batchId,
        status: 'success',
        formats: ['json'],
        output_paths: [`task2/exports/${batchId}.json`],
        created_at: new Date().toISOString(),
      };
    },
  };
}

export { MOCK_SUBMITTED_ANNOTATION };
