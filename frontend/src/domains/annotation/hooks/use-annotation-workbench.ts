import { useState, useCallback, useEffect, useRef } from 'react';
import { useApi } from '@foundation/providers/ApiProvider';
import type { AnnotationTask, AnnotationPayload } from '@foundation/types';
import { createBlankAnnotation, TaskStatus } from '@foundation/types';

const ANNOTATOR_ID = 'annotator_01';

export function useAnnotationWorkbench() {
  const api = useApi();
  const [task, setTask] = useState<AnnotationTask | null>(null);
  const [annotation, setAnnotation] = useState<AnnotationPayload>(createBlankAnnotation());
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const taskRef = useRef<AnnotationTask | null>(null);

  useEffect(() => {
    taskRef.current = task;
  }, [task]);

  const releaseCurrentTask = useCallback(
    async (reason: string, keepalive = false) => {
      const current = taskRef.current;
      if (!current || current.status !== TaskStatus.IN_PROGRESS) {
        return;
      }
      try {
        await api.releaseTask(current.task_id, ANNOTATOR_ID, { keepalive, reason });
      } catch {
        // release failures are non-fatal; timeout recovery still exists server-side
      } finally {
        taskRef.current = null;
        setTask(null);
        setDirty(false);
      }
    },
    [api]
  );

  const fetchNext = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (taskRef.current?.status === TaskStatus.IN_PROGRESS) {
        await releaseCurrentTask('fetch-next');
      }
      const nextTask = await api.getNextTask(ANNOTATOR_ID);
      setTask(nextTask);
      setAnnotation(nextTask.draft ?? createBlankAnnotation());
      setDirty(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No tasks available');
      setTask(null);
    } finally {
      setLoading(false);
    }
  }, [api, releaseCurrentTask]);

  const loadTask = useCallback(async (taskId: string) => {
    setLoading(true);
    setError(null);
    try {
      const t = await api.getTask(taskId);
      setTask(t);
      setAnnotation(t.draft ?? createBlankAnnotation());
      setDirty(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load task');
    } finally {
      setLoading(false);
    }
  }, [api]);

  const heartbeat = useCallback(async () => {
    const current = taskRef.current;
    if (!current || current.status !== TaskStatus.IN_PROGRESS) return;
    try {
      await api.heartbeatTask(current.task_id, ANNOTATOR_ID);
    } catch {
      // heartbeat failures are non-fatal; server timeout recovery still exists
    }
  }, [api]);

  const autosave = useCallback(async () => {
    if (!task || !dirty) return;
    setSaving(true);
    try {
      await api.autosaveTask(task.task_id, ANNOTATOR_ID, annotation);
      setDirty(false);
    } catch {
      // autosave failures are non-fatal
    } finally {
      setSaving(false);
    }
  }, [api, task, annotation, dirty]);

  const submit = useCallback(async () => {
    if (!task) return false;
    setLoading(true);
    setError(null);
    try {
      await api.submitTask(task.task_id, ANNOTATOR_ID, annotation);
      taskRef.current = null;
      setTask(null);
      setAnnotation(createBlankAnnotation());
      setDirty(false);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed');
      return false;
    } finally {
      setLoading(false);
    }
  }, [api, task, annotation]);

  const updateAnnotation = useCallback((partial: Partial<AnnotationPayload>) => {
    setDirty(true);
    setAnnotation((prev) => ({ ...prev, ...partial }));
  }, []);

  const skip = useCallback(async () => {
    await releaseCurrentTask('skip');
  }, [releaseCurrentTask]);

  useEffect(() => {
    const handlePageHide = () => {
      const current = taskRef.current;
      if (!current || current.status !== TaskStatus.IN_PROGRESS) return;
      void api.releaseTask(current.task_id, ANNOTATOR_ID, { keepalive: true, reason: 'pagehide' });
    };

    window.addEventListener('pagehide', handlePageHide);
    return () => {
      window.removeEventListener('pagehide', handlePageHide);
      void releaseCurrentTask('unmount', true);
    };
  }, [api, releaseCurrentTask]);

  return {
    task,
    annotation,
    loading,
    saving,
    dirty,
    error,
    fetchNext,
    loadTask,
    heartbeat,
    autosave,
    skip,
    submit,
    updateAnnotation,
  };
}
