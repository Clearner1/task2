import { useEffect } from 'react';
import { Button, Card, Spinner, EmptyState } from '@ui/index';
import type { AnnotationTask, PaginatedResponse } from '@foundation/types';
import '../review_export.css';

interface ReviewPanelProps {
  data: PaginatedResponse<AnnotationTask> | null;
  loading: boolean;
  onFetch: () => void;
  onApprove: (taskId: string) => void;
  onReject: (taskId: string) => void;
}

export function ReviewPanel({ data, loading, onFetch, onApprove, onReject }: ReviewPanelProps) {
  useEffect(() => {
    onFetch();
  }, [onFetch]);

  if (loading && !data) return <Spinner />;

  if (!data || data.items.length === 0) {
    return <EmptyState title="No submissions to review" description="All caught up!" />;
  }

  return (
    <div className="review-grid">
      {data.items.map((t) => {
        const annotation = t.draft;
        return (
          <Card key={t.task_id} className="review-task-card">
            <div className="review-task-card__header">
              <span className="review-task-card__id">{t.task_id}</span>
              <span style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)' }}>
                Media: {t.media_id}
              </span>
            </div>
            <div className="review-task-card__annotation">
              {annotation ? (
                <>
                  <strong>Emotion:</strong> {annotation.primary_emotion}<br />
                  <strong>Intensity:</strong> {annotation.intensity}/5 &nbsp;
                  <strong>Confidence:</strong> {annotation.confidence}/5<br />
                  <strong>Valence:</strong> {annotation.valence} &nbsp;
                  <strong>Arousal:</strong> {annotation.arousal}/5<br />
                  {annotation.notes && (
                    <>
                      <strong>Notes:</strong> {annotation.notes}
                    </>
                  )}
                </>
              ) : (
                <span style={{ color: 'var(--color-text-tertiary)' }}>No annotation payload found.</span>
              )}
            </div>
            <div className="review-task-card__actions">
              <Button variant="primary" size="sm" onClick={() => onApprove(t.task_id)} id={`btn-approve-${t.task_id}`}>
                ✓ Approve
              </Button>
              <Button variant="danger" size="sm" onClick={() => onReject(t.task_id)} id={`btn-reject-${t.task_id}`}>
                ✗ Reject
              </Button>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
