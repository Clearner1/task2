import { useState, useCallback } from 'react';
import { useApi } from '@foundation/providers/ApiProvider';
import type { AnnotationTask, AnnotationPayload } from '@foundation/types';
import { createBlankAnnotation } from '@foundation/types';

export function useAnnotationWorkbench() {
  const api = useApi();
  const [task, setTask] = useState<AnnotationTask | null>(null);
  const [annotation, setAnnotation] = useState<AnnotationPayload>(createBlankAnnotation());
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNext = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const nextTask = await api.getNextTask('annotator_01');
      setTask(nextTask);
      setAnnotation(nextTask.draft ?? createBlankAnnotation());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No tasks available');
      setTask(null);
    } finally {
      setLoading(false);
    }
  }, [api]);

  const loadTask = useCallback(async (taskId: string) => {
    setLoading(true);
    setError(null);
    try {
      const t = await api.getTask(taskId);
      setTask(t);
      setAnnotation(t.draft ?? createBlankAnnotation());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load task');
    } finally {
      setLoading(false);
    }
  }, [api]);

  const autosave = useCallback(async () => {
    if (!task) return;
    setSaving(true);
    try {
      await api.autosaveTask(task.task_id, 'annotator_01', annotation);
    } catch {
      // autosave failures are non-fatal
    } finally {
      setSaving(false);
    }
  }, [api, task, annotation]);

  const submit = useCallback(async () => {
    if (!task) return false;
    setLoading(true);
    setError(null);
    try {
      await api.submitTask(task.task_id, 'annotator_01', annotation);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Submission failed');
      return false;
    } finally {
      setLoading(false);
    }
  }, [api, task, annotation]);

  const updateAnnotation = useCallback((partial: Partial<AnnotationPayload>) => {
    setAnnotation((prev) => ({ ...prev, ...partial }));
  }, []);

  return {
    task,
    annotation,
    loading,
    saving,
    error,
    fetchNext,
    loadTask,
    autosave,
    submit,
    updateAnnotation,
  };
}
