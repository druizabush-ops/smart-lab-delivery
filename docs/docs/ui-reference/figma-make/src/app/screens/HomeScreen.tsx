import { Bell, FileText, Calendar, Gift, ClipboardList } from 'lucide-react';
import { ProfileCard } from '../components/ProfileCard';
import { MenuTile } from '../components/MenuTile';
import { BottomNavigation } from '../components/BottomNavigation';

interface HomeScreenProps {
  onNavigate: (screen: string) => void;
  activeTab: 'home' | 'results' | 'appointment' | 'promotions' | 'services';
  onTabChange: (tab: HomeScreenProps['activeTab']) => void;
}

export function HomeScreen({ onNavigate, activeTab, onTabChange }: HomeScreenProps) {
  return (
    <div className="min-h-screen bg-background pb-24">
      <header className="bg-white border-b border-border px-4 py-4 ">
        <div className="max-w-[390px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="none" className="w-6 h-6">
                <path d="M12 2L4 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-8-5z" fill="white" />
                <path d="M12 11a3 3 0 100-6 3 3 0 000 6zM12 12.5c-3.31 0-6 1.79-6 4v1.5h12V16.5c0-2.21-2.69-4-6-4z" fill="#16B1AC" />
              </svg>
            </div>
            <span className="text-xl font-bold text-primary">СМАРТ</span>
          </div>

          <button className="relative p-2 hover:bg-gray-100 rounded-full transition-colors">
            <Bell size={24} className="text-navy-text" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-error rounded-full"></span>
          </button>
        </div>
      </header>

      <main className="px-4 py-6 max-w-[390px] mx-auto space-y-4">
        <ProfileCard
          name="Иванов Иван Иванович"
          birthDate="15.04.1988 (38 лет)"
          phone="+7 (999) 123-45-67"
          email="ivanov@example.ru"
        />

        <div className="space-y-3">
          <MenuTile
            icon={<FileText size={24} className="text-primary" />}
            title="Результаты анализов"
            subtitle="Просмотр готовых и ожидающих исследований"
            bgColor="bg-mint-bg"
            onClick={() => onNavigate('results')}
          />

          <MenuTile
            icon={<Calendar size={24} className="text-info" />}
            title="Запись на прием"
            subtitle="Выберите врача и удобное время"
            bgColor="bg-sky-bg"
            onClick={() => onNavigate('appointment')}
          />

          <MenuTile
            icon={<Gift size={24} className="text-[#9333EA]" />}
            title="Бонусы и акции"
            subtitle="Программа лояльности и специальные предложения"
            bgColor="bg-lavender-bg"
            onClick={() => onNavigate('promotions')}
          />

          <MenuTile
            icon={<ClipboardList size={24} className="text-warning" />}
            title="Перечень услуг"
            subtitle="Полный список медицинских услуг"
            bgColor="bg-peach-bg"
            onClick={() => onNavigate('services')}
          />
        </div>
      </main>

      <BottomNavigation activeTab={activeTab} onTabChange={onTabChange} />
    </div>
  );
}
