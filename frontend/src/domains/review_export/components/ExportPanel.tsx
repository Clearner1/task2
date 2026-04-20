import { Button, Card, EmptyState } from '@ui/index';
import { formatTimestamp } from '@foundation/lib/format';
import type { ExportBatch } from '@foundation/types';
import '../review_export.css';

interface ExportPanelProps {
  batches: ExportBatch[];
  loading: boolean;
  onExportJson: () => void;
  onExportJsonl: () => void;
}

export function ExportPanel({ batches, loading, onExportJson, onExportJsonl }: ExportPanelProps) {
  return (
    <div className="export-section">
      <Card
        title="Export Reviewed Annotations"
        actions={
          <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
            <Button variant="primary" size="sm" onClick={onExportJson} loading={loading} id="btn-export-json">
              Export JSON
            </Button>
            <Button variant="secondary" size="sm" onClick={onExportJsonl} loading={loading} id="btn-export-jsonl">
              Export JSONL
            </Button>
          </div>
        }
      >
        {batches.length === 0 ? (
          <EmptyState title="No exports yet" description="Review annotations first, then export" />
        ) : (
          <div className="export-batches">
            {batches.map((b) => (
              <div key={b.batch_id} className="export-batch-row">
                <span className="export-batch-row__id">{b.batch_id}</span>
                <span className="export-batch-row__format">{b.formats.join(', ')}</span>
                <span className="export-batch-row__count">{b.status}</span>
                <span style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)', marginLeft: 'auto' }}>
                  {formatTimestamp(b.created_at)}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
