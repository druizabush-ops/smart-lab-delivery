import { ReactNode } from 'react';
import { Button } from './Button';

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
}

export function EmptyState({ icon, title, message, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-6 text-center">
      <div className="w-20 h-20 rounded-full bg-mint-bg flex items-center justify-center text-primary mb-4">
        {icon}
      </div>

      <h3 className="font-semibold text-[17px] text-navy-text mb-2">
        {title}
      </h3>

      <p className="text-[14px] text-secondary-text max-w-[280px] mb-6">
        {message}
      </p>

      {actionLabel && onAction && (
        <Button onClick={onAction} variant="primary">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
