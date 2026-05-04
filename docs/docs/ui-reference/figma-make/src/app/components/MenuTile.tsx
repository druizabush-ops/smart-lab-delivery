import { ReactNode } from 'react';
import { ChevronRight } from 'lucide-react';

interface MenuTileProps {
  icon: ReactNode;
  title: string;
  subtitle: string;
  bgColor: string;
  onClick: () => void;
}

export function MenuTile({ icon, title, subtitle, bgColor, onClick }: MenuTileProps) {
  return (
    <button
      onClick={onClick}
      className={`
        w-full p-5 rounded-[24px] text-left
        flex items-center gap-4
        transition-all active:scale-[0.98]
        ${bgColor}
      `}
    >
      <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center rounded-full bg-white/60">
        {icon}
      </div>

      <div className="flex-1 min-w-0">
        <h3 className="font-semibold text-[15px] text-navy-text">
          {title}
        </h3>
        <p className="text-[13px] text-secondary-text mt-0.5">
          {subtitle}
        </p>
      </div>

      <ChevronRight size={20} className="flex-shrink-0 text-secondary-text" />
    </button>
  );
}
