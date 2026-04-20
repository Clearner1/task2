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
        <p>Sentiment annotation pipeline overview</p>
      </div>

      <div className="dashboard-grid">
        <div className="stat-card">
          <span className="stat-card__value">{totalMedia}</span>
          <span className="stat-card__label">Total Media Files</span>
        </div>
        {stats.map((s) => (
          <div key={s.status} className={`stat-card ${s.cardClass}`}>
            <span className="stat-card__value">{s.count}</span>
            <span className="stat-card__label">{s.status.replace('_', ' ')}</span>
          </div>
        ))}
      </div>

      <Card title="Quick Start">
        <ol style={{ color: 'var(--color-text-secondary)', lineHeight: 2, paddingLeft: 'var(--space-lg)' }}>
          <li>Go to <strong>Media</strong> → Scan & Import audio/video files</li>
          <li>Click <strong>Preprocess</strong> to normalize imported media</li>
          <li>Go to <strong>Annotate</strong> → Get next task → Label emotions</li>
          <li>Go to <strong>Review</strong> → Approve or reject submissions</li>
          <li>Go to <strong>Export</strong> → Export approved annotations as JSON/JSONL</li>
        </ol>
      </Card>
    </div>
  );
}
