import type { ReactNode } from 'react';

interface ModalProps {
  open: boolean;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  onClose: () => void;
}

export function Modal({ open, title, children, footer, onClose }: ModalProps) {
  if (!open) return null;

  return (
    <div className="ui-modal-overlay" onClick={onClose}>
      <div className="ui-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ui-modal__header">{title}</div>
        <div className="ui-modal__body">{children}</div>
        {footer && <div className="ui-modal__footer">{footer}</div>}
      </div>
    </div>
  );
}
