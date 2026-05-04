import { Home, FileText, Calendar, Percent, ClipboardList } from 'lucide-react';

interface BottomNavigationProps {
  activeTab: 'home' | 'results' | 'appointment' | 'promotions' | 'services';
  onTabChange: (tab: BottomNavigationProps['activeTab']) => void;
}

export function BottomNavigation({ activeTab, onTabChange }: BottomNavigationProps) {
  const tabs = [
    { id: 'home' as const, label: 'Главная', Icon: Home },
    { id: 'results' as const, label: 'Анализы', Icon: FileText },
    { id: 'appointment' as const, label: 'Запись', Icon: Calendar },
    { id: 'promotions' as const, label: 'Акции', Icon: Percent },
    { id: 'services' as const, label: 'Услуги', Icon: ClipboardList },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-border ">
      <div className="flex items-center justify-around px-2 py-2 max-w-[390px] mx-auto">
        {tabs.map(({ id, label, Icon }) => {
          const isActive = activeTab === id;
          return (
            <button
              key={id}
              onClick={() => onTabChange(id)}
              className={`
                flex flex-col items-center gap-1 px-3 py-2 rounded-xl transition-all min-w-[60px]
                ${isActive ? 'text-primary' : 'text-secondary-text'}
              `}
            >
              <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
              <span className={`text-[11px] ${isActive ? 'font-semibold' : 'font-medium'}`}>
                {label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
