import type { ReactNode } from 'react';

interface CardProps {
  title?: string;
  actions?: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Card({ title, actions, footer, children, className = '' }: CardProps) {
  return (
    <div className={`ui-card ${className}`}>
      {title && (
        <div className="ui-card__header">
          <h3>{title}</h3>
          {actions && <div>{actions}</div>}
        </div>
      )}
      <div className="ui-card__body">{children}</div>
      {footer && <div className="ui-card__footer">{footer}</div>}
    </div>
  );
}
