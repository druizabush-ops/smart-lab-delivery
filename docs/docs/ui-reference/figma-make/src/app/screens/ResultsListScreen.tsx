import { useState } from 'react';
import { FileText } from 'lucide-react';
import { TopAppBar } from '../components/TopAppBar';
import { BottomNavigation } from '../components/BottomNavigation';
import { ResultCard } from '../components/ResultCard';
import { EmptyState } from '../components/EmptyState';
import { LoadingState } from '../components/LoadingState';
import { Status } from '../components/StatusChip';

interface Result {
  id: string;
  date: string;
  labName: string;
  status: Status;
}

interface ResultsListScreenProps {
  onNavigate: (screen: string, resultId?: string) => void;
  onBack: () => void;
  activeTab: 'home' | 'results' | 'appointment' | 'promotions' | 'services';
  onTabChange: (tab: ResultsListScreenProps['activeTab']) => void;
}

const mockResults: Result[] = [
  { id: '125487', date: '20.04.2024', labName: 'Гемотест', status: 'ready' },
  { id: '124003', date: '15.04.2024', labName: 'Гемотест', status: 'ready' },
  { id: '121562', date: '10.04.2024', labName: 'Инвитро', status: 'ready' },
  { id: '118945', date: '05.04.2024', labName: 'Гемотест', status: 'ready' },
  { id: '116231', date: '28.03.2024', labName: 'Инвитро', status: 'ready' },
  { id: '113009', date: '22.03.2024', labName: 'Гемотест', status: 'processing' },
];

export function ResultsListScreen({ onNavigate, onBack, activeTab, onTabChange }: ResultsListScreenProps) {
  const [loading, setLoading] = useState(false);
  const [results] = useState<Result[]>(mockResults);

  if (loading) {
    return (
      <div className="min-h-screen bg-background pb-24">
        <TopAppBar title="Результаты анализов" subtitle="Список ваших лабораторных исследований" onBack={onBack} />
        <div className="pt-24">
          <LoadingState />
        </div>
        <BottomNavigation activeTab={activeTab} onTabChange={onTabChange} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-24">
      <TopAppBar title="Результаты анализов" subtitle="Список ваших лабораторных исследований" onBack={onBack} />

      <main className="pt-24 px-4 pb-6 max-w-[390px] mx-auto">
        {results.length === 0 ? (
          <EmptyState
            icon={<FileText size={40} />}
            title="Пока нет доступных результатов"
            message="Когда лабораторные исследования будут готовы, они появятся здесь"
            actionLabel="Обновить"
            onAction={() => {}}
          />
        ) : (
          <div className="space-y-3">
            {results.map((result) => (
              <ResultCard
                key={result.id}
                resultId={result.id}
                date={result.date}
                labName={result.labName}
                status={result.status}
                onClick={() => onNavigate('result-details', result.id)}
              />
            ))}
          </div>
        )}
      </main>

      <BottomNavigation activeTab={activeTab} onTabChange={onTabChange} />
    </div>
  );
}
