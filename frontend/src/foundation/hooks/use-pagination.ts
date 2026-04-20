import { useState, useCallback } from 'react';

interface PaginationState {
  page: number;
  pageSize: number;
}

export function usePagination(initialPageSize = 20) {
  const [state, setState] = useState<PaginationState>({
    page: 1,
    pageSize: initialPageSize,
  });

  const setPage = useCallback((page: number) => {
    setState((prev) => ({ ...prev, page }));
  }, []);

  const setPageSize = useCallback((pageSize: number) => {
    setState({ page: 1, pageSize });
  }, []);

  const reset = useCallback(() => {
    setState({ page: 1, pageSize: initialPageSize });
  }, [initialPageSize]);

  return { ...state, setPage, setPageSize, reset };
}
