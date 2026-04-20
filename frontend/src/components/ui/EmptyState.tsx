interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
}

export function EmptyState({
  icon = '📭',
  title,
  description,
}: EmptyStateProps) {
  return (
    <div className="ui-empty">
      <div className="ui-empty__icon">{icon}</div>
      <div className="ui-empty__title">{title}</div>
      {description && <p>{description}</p>}
    </div>
  );
}
