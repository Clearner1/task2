import { useState, useCallback } from 'react';
import { useApi } from '@foundation/providers/ApiProvider';
import type { ExportBatch } from '@foundation/types';

export function useExport() {
  const api = useApi();
  const [batches, setBatches] = useState<ExportBatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const triggerExport = useCallback(
    async (formats: string[] = ['json']) => {
      setLoading(true);
      setError(null);
      try {
        const batch = await api.exportBatch({ formats });
        setBatches((prev) => [batch, ...prev]);
        return batch;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Export failed');
        return null;
      } finally {
        setLoading(false);
      }
    },
    [api],
  );

  return { batches, loading, error, triggerExport };
}
