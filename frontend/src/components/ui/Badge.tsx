import type { ReactNode } from 'react';

type BadgeStatus =
  | 'imported'
  | 'preprocessed'
  | 'ready'
  | 'in-progress'
  | 'submitted'
  | 'reviewed'
  | 'exported';

interface BadgeProps {
  status: BadgeStatus;
  children?: ReactNode;
}

const LABELS: Record<BadgeStatus, string> = {
  imported: 'Imported',
  preprocessed: 'Preprocessed',
  ready: 'Ready',
  'in-progress': 'In Progress',
  submitted: 'Submitted',
  reviewed: 'Reviewed',
  exported: 'Exported',
};

export function Badge({ status, children }: BadgeProps) {
  return (
    <span className={`ui-badge ui-badge--${status}`}>
      <StatusDot status={status} />
      {children ?? LABELS[status]}
    </span>
  );
}

function StatusDot({ status }: { status: BadgeStatus }) {
  const COLOR_MAP: Record<BadgeStatus, string> = {
    imported: 'var(--status-imported)',
    preprocessed: 'var(--status-preprocessed)',
    ready: 'var(--status-ready)',
    'in-progress': 'var(--status-in-progress)',
    submitted: 'var(--status-submitted)',
    reviewed: 'var(--status-reviewed)',
    exported: 'var(--status-exported)',
  };

  return (
    <span
      className="ui-status-dot"
      style={{ backgroundColor: COLOR_MAP[status] }}
    />
  );
}
