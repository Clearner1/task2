import { useEffect, useState } from 'react';
import { Card } from '@ui/index';
import { useApi } from '@foundation/providers/ApiProvider';
import type { TaskStatusType } from '@foundation/types';
import './pages.css';

interface StatusCount {
  status: TaskStatusType;
  count: number;
  color: string;
  cardClass: string;
}

export function DashboardPage() {
  const api = useApi();
  const [stats, setStats] = useState<StatusCount[]>([]);
  const [totalMedia, setTotalMedia] = useState(0);

  useEffect(() => {
    (async () => {
      const media = await api.listMedia({ page: 1, page_size: 1 });
      setTotalMedia(media.total);

      const tasks = await api.listTasks({ page: 1, page_size: 100 });
      const counts: Record<string, number> = {};
      tasks.items.forEach((t) => {
        counts[t.status] = (counts[t.status] || 0) + 1;
      });

      setStats([
        { status: 'READY' as TaskStatusType, count: counts['READY'] || 0, color: 'var(--status-ready)', cardClass: 'stat-card--success' },
        { status: 'IN_PROGRESS' as TaskStatusType, count: counts['IN_PROGRESS'] || 0, color: 'var(--status-in-progress)', cardClass: 'stat-card--info' },
        { status: 'SUBMITTED' as TaskStatusType, count: counts['SUBMITTED'] || 0, color: 'var(--status-submitted)', cardClass: 'stat-card--warning' },
        { status: 'REVIEWED' as TaskStatusType, count: counts['REVIEWED'] || 0, color: 'var(--color-accent-400)', cardClass: '' },
        { status: 'EXPORTED' as TaskStatusType, count: counts['EXPORTED'] || 0, color: 'var(--status-exported)', cardClass: 'stat-card--success' },
      ]);
    })();
  }, [api]);

  return (
    <div className="animate-fade-in">
      <div className="page-header">
        <h2>Dashboard</h2>
        <p>Operational overview of ingestion, normalization, annotation, review, and export.</p>
      </div>

      <div className="dashboard-grid">
        <div className="stat-card stat-card--hero">
          <span className="stat-card__eyebrow">Task2 Control Room</span>
          <div className="stat-card__headline">
            <span>Human review stays central.</span>
            <span>The pipeline stays disciplined.</span>
          </div>
          <div className="stat-card__copy">
            Import source media, normalize it into workbench-ready assets, then move each task through annotation, review, and export with visible state changes.
          </div>
        </div>
        <div className="stat-card">
          <span className="stat-card__value">{totalMedia}</span>
          <span className="stat-card__label">Media In Archive</span>
        </div>
        {stats.map((s) => (
          <div key={s.status} className={`stat-card ${s.cardClass}`}>
            <span className="stat-card__value">{s.count}</span>
            <span className="stat-card__label">{s.status.replace('_', ' ')}</span>
          </div>
        ))}
      </div>

      <div className="dashboard-notes">
        <Card title="Workflow Cadence">
          <ol className="quick-start-list">
            <li>Go to <strong>Media</strong> and import raw audio or video from the configured ingest directory.</li>
            <li>Run <strong>Preprocess</strong> to generate normalized playable assets and support files.</li>
            <li>Open <strong>Annotate</strong> to pull the next ready task and record emotion labels.</li>
            <li>Use <strong>Review</strong> as the quality gate before release.</li>
            <li>Finalize in <strong>Export</strong> with JSON or JSONL output.</li>
          </ol>
        </Card>

        <Card title="Operational Notes">
          <div className="ops-list">
            <div className="ops-list__row">
              <span className="ops-list__label">Playback Source</span>
              <span className="ops-list__value">Normalized asset first</span>
            </div>
            <div className="ops-list__row">
              <span className="ops-list__label">Task Ownership</span>
              <span className="ops-list__value">Lease + heartbeat</span>
            </div>
            <div className="ops-list__row">
              <span className="ops-list__label">Review Policy</span>
              <span className="ops-list__value">Approve before export</span>
            </div>
            <div className="ops-list__row">
              <span className="ops-list__label">Runtime Target</span>
              <span className="ops-list__value">24h unattended</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
