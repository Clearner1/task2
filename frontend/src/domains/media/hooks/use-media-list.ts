import { useState, useCallback } from 'react';
import { useApi } from '@foundation/providers/ApiProvider';
import type { MediaRecord, PaginatedResponse } from '@foundation/types';

export function useMediaList() {
  const api = useApi();
  const [data, setData] = useState<PaginatedResponse<MediaRecord> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(
    async (params: { page?: number; page_size?: number; status?: string } = {}) => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.listMedia(params);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load media');
      } finally {
        setLoading(false);
      }
    },
    [api],
  );

  const importMedia = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.importMedia();
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, [api]);

  const preprocessMedia = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.preprocessMedia();
      return result;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Preprocess failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, [api]);

  return { data, loading, error, fetch, importMedia, preprocessMedia };
}
