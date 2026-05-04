import { useState } from 'react';
import { TestTube, Stethoscope, Pill, Activity, Eye, Heart, Ear, Baby, ChevronRight, ChevronDown, FileText } from 'lucide-react';
import { TopAppBar } from '../components/TopAppBar';
import { BottomNavigation } from '../components/BottomNavigation';
import { SearchInput } from '../components/SearchInput';

interface ServicesScreenProps {
  onBack: () => void;
  activeTab: 'home' | 'results' | 'appointment' | 'promotions' | 'services';
  onTabChange: (tab: ServicesScreenProps['activeTab']) => void;
}

const categories = [
  { name: 'Анализы', icon: TestTube, count: 150, color: 'text-primary', bg: 'bg-mint-bg' },
  { name: 'Направления врачей', icon: Stethoscope, count: 25, color: 'text-info', bg: 'bg-sky-bg' },
  { name: 'Стоматология', icon: Pill, count: 32, color: 'text-[#9333EA]', bg: 'bg-lavender-bg' },
  { name: 'УЗИ', icon: Activity, count: 18, color: 'text-warning', bg: 'bg-peach-bg' },
  { name: 'Функциональная диагностика', icon: Heart, count: 12, color: 'text-error', bg: 'bg-error-light' },
  { name: 'Гинекология', icon: Baby, count: 24, color: 'text-primary', bg: 'bg-mint-bg' },
  { name: 'ЛОР', icon: Ear, count: 15, color: 'text-info', bg: 'bg-sky-bg' },
  { name: 'Офтальмология', icon: Eye, count: 10, color: 'text-[#9333EA]', bg: 'bg-lavender-bg' },
];

interface TreeFolder {
  name: string;
  count: number;
  services?: { name: string; price: number }[];
}

const treeFolders: TreeFolder[] = [
  { name: 'Гематологические исследования', count: 15 },
  { name: 'Биохимические исследования', count: 28 },
  {
    name: 'Гормональные исследования',
    count: 22,
    services: [
      { name: 'ТТГ (тиреотропный гормон)', price: 250 },
      { name: 'Т3 свободный', price: 280 },
      { name: 'Т4 свободный', price: 280 },
      { name: 'Пролактин', price: 300 },
      { name: 'Кортизол', price: 320 },
    ]
  },
  { name: 'Общие клинические исследования', count: 35 },
  { name: 'Иммунологические исследования', count: 18 },
];

export function ServicesScreen({ onBack, activeTab, onTabChange }: ServicesScreenProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedFolder, setExpandedFolder] = useState<string | null>('Гормональные исследования');

  return (
    <div className="min-h-screen bg-background pb-24">
      <TopAppBar
        title="Перечень услуг"
        subtitle="Полный список медицинских услуг"
        onBack={onBack}
      />

      <main className="pt-20 px-4 pb-6 max-w-[390px] mx-auto">
        <div className="mb-4">
          <SearchInput
            placeholder="Поиск услуги"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClear={() => setSearchQuery('')}
          />
          <p className="text-xs text-secondary-text mt-2 px-1">
            Поиск осуществляется по мере ввода
          </p>
        </div>

        <div className="mb-5">
          <h3 className="font-semibold text-[15px] text-navy-text mb-3 px-1">
            Категории услуг
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {categories.map((category) => {
              const Icon = category.icon;
              return (
                <button
                  key={category.name}
                  className={`${category.bg} rounded-[20px] p-4 text-left transition-all active:scale-[0.98]`}
                >
                  <div className={`w-10 h-10 rounded-full bg-white/60 flex items-center justify-center mb-3 ${category.color}`}>
                    <Icon size={20} />
                  </div>
                  <h4 className="font-semibold text-[13px] text-navy-text mb-1 leading-tight">
                    {category.name}
                  </h4>
                  <p className="text-[11px] text-secondary-text">
                    {category.count} услуг
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        <div className="bg-white rounded-[24px] border border-border overflow-hidden">
          <div className="p-4 border-b border-divider flex items-center justify-between">
            <div>
              <h4 className="font-semibold text-[15px] text-navy-text">Анализы</h4>
              <p className="text-xs text-secondary-text mt-0.5">150 услуг</p>
            </div>
          </div>

          <div>
            {treeFolders.map((folder) => {
              const isExpanded = expandedFolder === folder.name;
              return (
                <div key={folder.name}>
                  <button
                    onClick={() => setExpandedFolder(isExpanded ? null : folder.name)}
                    className="w-full px-4 py-3 flex items-center gap-3 hover:bg-gray-50 transition-colors border-b border-divider"
                  >
                    <div className="w-8 h-8 rounded-lg bg-mint-bg flex items-center justify-center flex-shrink-0">
                      {isExpanded ? (
                        <ChevronDown size={18} className="text-primary" />
                      ) : (
                        <ChevronRight size={18} className="text-primary" />
                      )}
                    </div>
                    <div className="flex-1 text-left">
                      <div className="font-medium text-[14px] text-navy-text">{folder.name}</div>
                      <div className="text-[12px] text-secondary-text mt-0.5">{folder.count} услуг</div>
                    </div>
                  </button>

                  {isExpanded && folder.services && (
                    <div className="bg-gray-50">
                      {folder.services.map((service, idx) => (
                        <div
                          key={idx}
                          className="px-4 py-3 flex items-center gap-3 border-b border-divider last:border-b-0"
                        >
                          <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center flex-shrink-0">
                            <FileText size={16} className="text-primary" />
                          </div>
                          <div className="flex-1">
                            <div className="text-[13px] text-navy-text">{service.name}</div>
                          </div>
                          <div className="font-semibold text-[14px] text-primary">
                            {service.price} ₽
                          </div>
                        </div>
                      ))}
                      <button className="w-full px-4 py-3 text-sm font-medium text-primary hover:bg-white transition-colors">
                        Показать все ({folder.count})
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </main>

      <BottomNavigation activeTab={activeTab} onTabChange={onTabChange} />
    </div>
  );
}
