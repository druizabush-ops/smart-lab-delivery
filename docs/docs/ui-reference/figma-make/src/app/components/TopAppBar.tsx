import { ArrowLeft, Filter } from 'lucide-react';

interface TopAppBarProps {
  title: string;
  subtitle?: string;
  onBack?: () => void;
  rightAction?: 'filter' | null;
  onRightAction?: () => void;
}

export function TopAppBar({ title, subtitle, onBack, rightAction, onRightAction }: TopAppBarProps) {
  return (
    <header className="fixed top-0 left-0 right-0 bg-white border-b border-border z-10 ">
      <div className="flex items-center justify-between px-4 py-3 max-w-[390px] mx-auto min-h-[56px]">
        {onBack && (
          <button
            onClick={onBack}
            className="p-2 -ml-2 text-navy-text hover:bg-gray-100 rounded-full transition-colors"
          >
            <ArrowLeft size={24} />
          </button>
        )}

        <div className={`flex-1 ${onBack ? 'ml-3' : ''}`}>
          <h1 className="font-semibold text-[17px] text-navy-text leading-tight">{title}</h1>
          {subtitle && (
            <p className="text-[13px] text-secondary-text mt-0.5">{subtitle}</p>
          )}
        </div>

        {rightAction === 'filter' && (
          <button
            onClick={onRightAction}
            className="p-2 text-primary hover:bg-primary-light rounded-full transition-colors"
          >
            <Filter size={20} />
          </button>
        )}
      </div>
    </header>
  );
}
