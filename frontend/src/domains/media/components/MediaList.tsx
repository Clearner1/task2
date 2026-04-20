import { Badge, Pagination, Spinner, EmptyState } from '@ui/index';
import { formatDuration, formatTimestamp } from '@foundation/lib/format';
import { statusToBadgeKey } from '@foundation/types';
import type { MediaRecord, PaginatedResponse } from '@foundation/types';
import '../media.css';

interface MediaListProps {
  data: PaginatedResponse<MediaRecord> | null;
  loading: boolean;
  page: number;
  onPageChange: (page: number) => void;
}

export function MediaList({ data, loading, page, onPageChange }: MediaListProps) {
  if (loading && !data) return <Spinner />;
  if (!data || data.items.length === 0) {
    return <EmptyState icon="🎵" title="No media files" description="Import media to get started" />;
  }

  return (
    <div className="animate-fade-in">
      <table className="media-list-table">
        <thead>
          <tr>
            <th>Media ID</th>
            <th>Type</th>
            <th>Format</th>
            <th>Duration</th>
            <th>Status</th>
            <th>Updated</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((m) => (
            <tr key={m.media_id}>
              <td className="media-id-cell">{m.media_id}</td>
              <td>{m.media_type}</td>
              <td>{m.detected_format}</td>
              <td className="duration-cell">{formatDuration(m.duration_ms)}</td>
              <td>
                <Badge status={statusToBadgeKey(m.status)} />
              </td>
              <td style={{ color: 'var(--color-text-tertiary)', fontSize: 'var(--font-size-xs)' }}>
                {formatTimestamp(m.updated_at)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <Pagination
        page={page}
        pageSize={data.page_size}
        total={data.total}
        onPageChange={onPageChange}
      />
    </div>
  );
}
