import { Button, Card, MediaPlayer, Spinner, EmptyState } from '@ui/index';
import { Badge } from '@ui/index';
import { useAutosave } from '@foundation/hooks/use-autosave';
import { useApi } from '@foundation/providers/ApiProvider';
import { formatDuration } from '@foundation/lib/format';
import { statusToBadgeKey } from '@foundation/types';
import type { AnnotationTask, AnnotationPayload, TaskStatusType } from '@foundation/types';
import { AnnotationForm } from './AnnotationForm';
import '../annotation.css';

interface AnnotationWorkbenchProps {
  task: AnnotationTask | null;
  annotation: AnnotationPayload;
  loading: boolean;
  saving: boolean;
  error: string | null;
  onFetchNext: () => void;
  onAutosave: () => void;
  onSubmit: () => void;
  onUpdateAnnotation: (partial: Partial<AnnotationPayload>) => void;
}

const AUTOSAVE_INTERVAL = 15_000; // 15s from config

export function AnnotationWorkbench({
  task,
  annotation,
  loading,
  saving,
  error,
  onFetchNext,
  onAutosave,
  onSubmit,
  onUpdateAnnotation,
}: AnnotationWorkbenchProps) {
  const api = useApi();

  // Autosave while task is active
  useAutosave(onAutosave, AUTOSAVE_INTERVAL, !!task);

  if (loading) return <Spinner />;

  if (!task) {
    return (
      <div className="workbench-empty">
        <EmptyState
          icon="🎧"
          title={error || 'Ready to annotate'}
          description={error ? 'Try again or check the task list' : 'Click below to get the next available task'}
        />
        <Button variant="primary" size="lg" onClick={onFetchNext} id="btn-get-next-task" loading={loading}>
          ▶ Get Next Task
        </Button>
      </div>
    );
  }

  const mediaUrl = api.getMediaStreamUrl(task.media_id);
  const mediaType = task.media?.media_type ?? 'audio';

  return (
    <div className="workbench">
      {/* Left: Player + Info */}
      <div className="workbench__player-section">
        <Card title="Media Playback">
          <div className="workbench__info">
            <div>
              <div className="workbench__info-id">{task.media_id}</div>
              <div className="workbench__info-meta">
                {mediaType} · {formatDuration(task.media?.duration_ms ?? null)}
              </div>
            </div>
            <Badge status={statusToBadgeKey(task.status as TaskStatusType)} />
          </div>
          <div style={{ marginTop: 'var(--space-md)' }}>
            <MediaPlayer
              id="workbench-player"
              src={mediaUrl}
              type={mediaType}
              label={task.media?.source_path}
            />
          </div>
        </Card>

        {/* Autosave indicator */}
        <div className="autosave-indicator">
          <span className={`autosave-dot ${saving ? 'autosave-dot--saving' : ''}`} />
          {saving ? 'Saving draft...' : 'Autosave active'}
        </div>
      </div>

      {/* Right: Annotation form */}
      <Card
        title="Annotation"
        footer={
          <div className="workbench__actions" style={{ width: '100%' }}>
            <Button variant="secondary" onClick={onFetchNext} id="btn-skip-task">
              Skip
            </Button>
            <Button
              variant="primary"
              onClick={onSubmit}
              id="btn-submit-annotation"
              disabled={!annotation.primary_emotion}
              loading={loading}
              style={{ marginLeft: 'auto' }}
            >
              ✓ Submit
            </Button>
          </div>
        }
      >
        <AnnotationForm value={annotation} onChange={onUpdateAnnotation} />
      </Card>
    </div>
  );
}
