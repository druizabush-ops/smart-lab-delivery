import { TopAppBar } from '../components/TopAppBar';
import { BottomNavigation } from '../components/BottomNavigation';
import { StatusChip } from '../components/StatusChip';
import { Button } from '../components/Button';
import { FileText } from 'lucide-react';

interface ResultDetailsScreenProps {
  resultId: string;
  onNavigate: (screen: string) => void;
  onBack: () => void;
  activeTab: 'home' | 'results' | 'appointment' | 'promotions' | 'services';
  onTabChange: (tab: ResultDetailsScreenProps['activeTab']) => void;
}

interface AnalysisItem {
  name: string;
  code?: string;
  value: string;
  unit: string;
  normalRange: string;
  date: string;
}

interface AnalysisGroup {
  title: string;
  items: AnalysisItem[];
}

const mockData: AnalysisGroup[] = [
  {
    title: 'Биохимические исследования крови',
    items: [
      { name: 'Холестерин общий', code: 'A09.05.009', value: '4.2', unit: 'ммоль/л', normalRange: '3.5 - 5.2', date: '20.04.2024' },
      { name: 'Глюкоза венозной плазмы', code: 'A09.05.023', value: '5.383', unit: 'ммоль/л', normalRange: '3.88 - 5.83', date: '20.04.2024' },
    ]
  },
  {
    title: 'Гормональные исследования крови',
    items: [
      { name: 'ТТГ (Тиреотропный гормон)', value: '3.24μIU/ml', unit: '', normalRange: '0 - 29.9', date: '20.04.2024' },
    ]
  },
  {
    title: 'Пренатальная диагностика',
    items: [
      { name: 'бета-ХГЧ', value: '0.2', unit: 'ng/ml', normalRange: 'Смотреть текст', date: '20.04.2024' },
      { name: 'Эстриол свободный', value: '0.19', unit: 'ng/ml', normalRange: '', date: '20.04.2024' },
      { name: 'АФП', value: '31.32', unit: 'ng/ml', normalRange: '', date: '20.04.2024' },
    ]
  }
];

export function ResultDetailsScreen({ resultId, onNavigate, onBack, activeTab, onTabChange }: ResultDetailsScreenProps) {
  return (
    <div className="min-h-screen bg-background pb-32">
      <TopAppBar
        title={`Исследование №${resultId}`}
        subtitle="20.04.2024"
        onBack={onBack}
      />

      <main className="pt-20 px-4 pb-6 max-w-[390px] mx-auto">
        <div className="mb-4 flex items-center justify-between">
          <StatusChip status="ready" />
        </div>

        <div className="space-y-5">
          {mockData.map((group, idx) => (
            <div key={idx} className="bg-white rounded-[20px] p-5 border border-border">
              <h3 className="font-semibold text-[15px] text-navy-text mb-4">
                {group.title}
              </h3>

              <div className="space-y-4">
                {group.items.map((item, itemIdx) => (
                  <div key={itemIdx} className={`pb-4 ${itemIdx !== group.items.length - 1 ? 'border-b border-divider' : ''}`}>
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <p className="font-medium text-[14px] text-navy-text">
                          {item.name}
                        </p>
                        {item.code && (
                          <p className="text-[12px] text-muted-text mt-0.5">
                            {item.code}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3 text-[13px]">
                      <div>
                        <p className="text-secondary-text mb-1">Значение</p>
                        <p className="font-semibold text-navy-text">{item.value}</p>
                      </div>
                      <div>
                        <p className="text-secondary-text mb-1">Единицы</p>
                        <p className="text-navy-text">{item.unit || '—'}</p>
                      </div>
                      <div>
                        <p className="text-secondary-text mb-1">Норма</p>
                        <p className="text-navy-text">{item.normalRange || '—'}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6">
          <Button
            variant="primary"
            size="large"
            className="w-full"
            onClick={() => onNavigate('pdf-viewer')}
          >
            <div className="flex items-center justify-center gap-2">
              <FileText size={20} />
              <span>Открыть в PDF</span>
            </div>
          </Button>
        </div>
      </main>

      <BottomNavigation activeTab={activeTab} onTabChange={onTabChange} />
    </div>
  );
}
