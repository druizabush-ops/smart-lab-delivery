import { Check, Clock, X, AlertCircle } from 'lucide-react';

export type Status = 'ready' | 'processing' | 'canceled' | 'error';

interface StatusChipProps {
  status: Status;
}

export function StatusChip({ status }: StatusChipProps) {
  const configs = {
    ready: {
      label: 'Готово',
      bg: 'bg-success-light',
      text: 'text-success',
      Icon: Check
    },
    processing: {
      label: 'В обработке',
      bg: 'bg-info-light',
      text: 'text-info',
      Icon: Clock
    },
    canceled: {
      label: 'Отменено',
      bg: 'bg-gray-100',
      text: 'text-gray-600',
      Icon: X
    },
    error: {
      label: 'Ошибка',
      bg: 'bg-error-light',
      text: 'text-error',
      Icon: AlertCircle
    }
  };

  const config = configs[status];
  const Icon = config.Icon;

  return (
    <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full ${config.bg}`}>
      <Icon size={14} className={config.text} />
      <span className={`text-[13px] font-medium ${config.text}`}>
        {config.label}
      </span>
    </div>
  );
}
