import { FileText, ChevronRight } from 'lucide-react';
import { StatusChip, Status } from './StatusChip';

interface ResultCardProps {
  resultId: string;
  date: string;
  labName?: string;
  status: Status;
  onClick: () => void;
}

export function ResultCard({ resultId, date, labName, status, onClick }: ResultCardProps) {
  return (
    <button
      onClick={onClick}
      disabled={status === 'error' || status === 'canceled'}
      className={`
        w-full p-4 bg-white rounded-[20px] border border-border
        flex items-center gap-4
        transition-all active:scale-[0.98]
        ${(status === 'error' || status === 'canceled') ? 'opacity-60' : ''}
      `}
    >
      <div className="flex-shrink-0 w-12 h-12 rounded-full bg-mint-bg flex items-center justify-center">
        <FileText size={24} className="text-primary" />
      </div>

      <div className="flex-1 min-w-0 text-left">
        <div className="font-semibold text-[15px] text-navy-text">
          {resultId}
        </div>
        <div className="text-[13px] text-secondary-text mt-1">
          {date}
        </div>
        {labName && (
          <div className="text-[12px] text-muted-text mt-0.5">
            {labName}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <StatusChip status={status} />
        {status === 'ready' && (
          <ChevronRight size={20} className="text-secondary-text" />
        )}
      </div>
    </button>
  );
}
