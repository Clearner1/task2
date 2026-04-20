import { useEffect, useRef } from 'react';

/**
 * Autosave hook — calls `saveFn` at a regular interval while `active` is true.
 * Returns a ref to the latest save function to avoid stale closures.
 */
export function useAutosave(
  saveFn: () => void | Promise<void>,
  intervalMs: number,
  active: boolean,
) {
  const savedFn = useRef(saveFn);

  useEffect(() => {
    savedFn.current = saveFn;
  }, [saveFn]);

  useEffect(() => {
    if (!active || intervalMs <= 0) return;

    const id = setInterval(() => {
      savedFn.current();
    }, intervalMs);

    return () => clearInterval(id);
  }, [active, intervalMs]);
}
