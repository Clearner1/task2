import { useState, useCallback } from 'react';
import { useApi } from '@foundation/providers/ApiProvider';
import type { TaskItem, PaginatedResponse } from '@foundation/types';

export function useTaskList() {
  const api = useApi();
  const [data, setData] = useState<PaginatedResponse<TaskItem> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(
    async (params: { page?: number; page_size?: number; status?: string } = {}) => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.listTasks(params);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load tasks');
      } finally {
        setLoading(false);
      }
    },
    [api],
  );

  return { data, loading, error, fetch };
}
