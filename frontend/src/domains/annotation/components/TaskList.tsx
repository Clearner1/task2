import { Badge, Pagination, Spinner, EmptyState, Select } from '@ui/index';
import { formatTimestamp } from '@foundation/lib/format';
import { statusToBadgeKey, TaskStatus } from '@foundation/types';
import type { TaskItem, PaginatedResponse, TaskStatusType } from '@foundation/types';
import '../annotation.css';

interface TaskListProps {
  data: PaginatedResponse<TaskItem> | null;
  loading: boolean;
  page: number;
  statusFilter: string;
  onPageChange: (page: number) => void;
  onStatusFilterChange: (status: string) => void;
  onSelectTask: (taskId: string) => void;
}

const STATUS_OPTIONS = [
  { value: '', label: 'All Statuses' },
  ...Object.values(TaskStatus).map((s) => ({ value: s, label: s.replace('_', ' ') })),
];

export function TaskList({
  data,
  loading,
  page,
  statusFilter,
  onPageChange,
  onStatusFilterChange,
  onSelectTask,
}: TaskListProps) {
  return (
    <div>
      <div className="task-filter-bar">
        <Select
          id="filter-status"
          label="Filter by Status"
          value={statusFilter}
          options={STATUS_OPTIONS}
          onChange={onStatusFilterChange}
        />
      </div>

      {loading && !data ? (
        <Spinner />
      ) : !data || data.items.length === 0 ? (
        <EmptyState icon="📋" title="No tasks found" description="Import and preprocess media first" />
      ) : (
        <div className="animate-fade-in">
          <table className="task-list-table">
            <thead>
              <tr>
                <th>Task ID</th>
                <th>Media ID</th>
                <th>Status</th>
                <th>Assigned To</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((t) => (
                <tr key={t.task_id} onClick={() => onSelectTask(t.task_id)}>
                  <td className="task-id-cell">{t.task_id}</td>
                  <td style={{ color: 'var(--color-accent-400)', fontFamily: 'monospace', fontSize: 'var(--font-size-xs)' }}>
                    {t.media_id}
                  </td>
                  <td>
                    <Badge status={statusToBadgeKey(t.status as TaskStatusType)} />
                  </td>
                  <td style={{ color: 'var(--color-text-secondary)' }}>
                    {t.assigned_to || '—'}
                  </td>
                  <td style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)' }}>
                    {formatTimestamp(t.updated_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} pageSize={data.page_size} total={data.total} onPageChange={onPageChange} />
        </div>
      )}
    </div>
  );
}
