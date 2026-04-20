import { Button, Card } from '@ui/index';

interface ImportPanelProps {
  loading: boolean;
  mediaCount: number;
  onImport: () => void;
  onPreprocess: () => void;
}

export function ImportPanel({ loading, mediaCount, onImport, onPreprocess }: ImportPanelProps) {
  return (
    <Card title="Media Pipeline" actions={
      <div style={{ display: 'flex', gap: 'var(--space-sm)' }}>
        <Button variant="primary" size="sm" loading={loading} onClick={onImport} id="btn-import">
          ↓ Scan & Import
        </Button>
        <Button variant="secondary" size="sm" loading={loading} onClick={onPreprocess} id="btn-preprocess">
          ⚙ Preprocess
        </Button>
      </div>
    }>
      <div className="import-panel">
        <div className="import-panel__stat">
          <span className="import-panel__stat-value">{mediaCount}</span>
          <span className="import-panel__stat-label">Total Media</span>
        </div>
      </div>
    </Card>
  );
}
