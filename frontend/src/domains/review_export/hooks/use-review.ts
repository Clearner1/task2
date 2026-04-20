import { useState, useCallback } from 'react';
import { useApi } from '@foundation/providers/ApiProvider';
import type { AnnotationTask, PaginatedResponse } from '@foundation/types';

export function useReview() {
  const api = useApi();
  const [submittedTasks, setSubmittedTasks] = useState<PaginatedResponse<AnnotationTask> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSubmitted = useCallback(
    async (params: { page?: number; page_size?: number } = {}) => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.listTasks({ ...params, status: 'SUBMITTED' });
        const detailedItems = await Promise.all(
          result.items.map(async (item) => {
            try {
              return await api.getTask(item.task_id);
            } catch {
              return { ...item, media: undefined, draft: null } as unknown as AnnotationTask;
            }
          })
        );
        setSubmittedTasks({ ...result, items: detailedItems });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load submitted tasks');
      } finally {
        setLoading(false);
      }
    },
    [api],
  );

  const approve = useCallback(
    async (taskId: string) => {
      setLoading(true);
      try {
        await api.reviewTask(taskId, { decision: 'approved', reviewer_id: 'reviewer_01' });
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Review failed');
        return false;
      } finally {
        setLoading(false);
      }
    },
    [api],
  );

  const reject = useCallback(
    async (taskId: string, notes?: string) => {
      setLoading(true);
      try {
        await api.reviewTask(taskId, { decision: 'rejected', reviewer_id: 'reviewer_01', notes });
        return true;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Review failed');
        return false;
      } finally {
        setLoading(false);
      }
    },
    [api],
  );

  return { submittedTasks, loading, error, fetchSubmitted, approve, reject };
}
