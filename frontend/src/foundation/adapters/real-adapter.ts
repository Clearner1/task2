import type { ApiAdapter } from './types';
import type {
  MediaRecord,
  PaginatedResponse,
  ReviewDecision,
  ExportBatch,
  TaskItem,
  TaskDetail,
} from '../types';
import { flattenTaskDetail } from '../types';

/* =============== HTTP Client =============== */

const DEFAULT_BASE = '/api';

class HttpError extends Error {
  status: number;
  body: { code: string; message: string; entity_id?: string; retryable: boolean };

  constructor(
    status: number,
    body: { code: string; message: string; entity_id?: string; retryable: boolean },
  ) {
    super(body.message);
    this.name = 'HttpError';
    this.status = status;
    this.body = body;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${DEFAULT_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const body = (await res.json().catch(() => ({
      code: 'UNKNOWN',
      message: res.statusText,
      retryable: false,
    }))) as { code: string; message: string; entity_id?: string; retryable: boolean };
    throw new HttpError(res.status, body);
  }

  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

async function sendNoContentRequest(path: string, options: RequestInit = {}): Promise<void> {
  const url = `${DEFAULT_BASE}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const body = (await res.json().catch(() => ({
      code: 'UNKNOWN',
      message: res.statusText,
      retryable: false,
    }))) as { code: string; message: string; entity_id?: string; retryable: boolean };
    throw new HttpError(res.status, body);
  }
}

function qs(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined);
  if (entries.length === 0) return '';
  return '?' + entries.map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`).join('&');
}

/* =============== Real Adapter =============== */

export function createRealAdapter(): ApiAdapter {
  return {
    listMedia(params) {
      return request<PaginatedResponse<MediaRecord>>(`/media${qs(params)}`);
    },
    getMedia(mediaId) {
      return request<MediaRecord>(`/media/${mediaId}`);
    },
    importMedia() {
      return request<{ imported: number; existing: number }>('/media/import', { method: 'POST' });
    },
    preprocessMedia() {
      return request<{ processed: number; failed: number }>('/media/preprocess', { method: 'POST' });
    },
    getMediaStreamUrl(mediaId) {
      return `${DEFAULT_BASE}/media/${mediaId}/stream`;
    },

    listTasks(params) {
      return request<PaginatedResponse<TaskItem>>(`/tasks${qs(params)}`);
    },
    async getNextTask(annotatorId = 'annotator_01') {
      const detail = await request<TaskDetail | null>(`/tasks/next?annotator_id=${encodeURIComponent(annotatorId)}`);
      if (!detail) {
        throw new Error('No tasks available');
      }
      return flattenTaskDetail(detail);
    },
    async getTask(taskId) {
      const detail = await request<TaskDetail>(`/tasks/${taskId}`);
      return flattenTaskDetail(detail);
    },
    async heartbeatTask(taskId, annotatorId) {
      await request<unknown>(`/tasks/${taskId}/heartbeat`, {
        method: 'POST',
        body: JSON.stringify({ annotator_id: annotatorId, reason: 'active-editing' }),
      });
    },
    async autosaveTask(taskId, annotatorId, payload) {
      await request<unknown>(`/tasks/${taskId}/autosave`, {
        method: 'POST',
        body: JSON.stringify({ annotator_id: annotatorId, annotation: payload }),
      });
    },
    async releaseTask(taskId, annotatorId, options) {
      await sendNoContentRequest(`/tasks/${taskId}/release`, {
        method: 'POST',
        keepalive: options?.keepalive,
        body: JSON.stringify({ annotator_id: annotatorId, reason: options?.reason ?? 'abandon' }),
      });
    },
    async submitTask(taskId, annotatorId, payload) {
      await request<unknown>(`/tasks/${taskId}/submit`, {
        method: 'POST',
        body: JSON.stringify({ annotator_id: annotatorId, annotation: payload }),
      });
    },

    reviewTask(taskId, decision) {
      return request<ReviewDecision>(`/reviews/${taskId}`, {
        method: 'POST',
        body: JSON.stringify(decision),
      });
    },
    exportBatch(params) {
      return request<ExportBatch>('/exports', {
        method: 'POST',
        body: JSON.stringify(params),
      });
    },
    getExportBatch(batchId) {
      return request<ExportBatch>(`/exports/${batchId}`);
    },
  };
}

export { HttpError };
