import { Gift, TrendingUp, Award, Settings } from 'lucide-react';
import { TopAppBar } from '../components/TopAppBar';
import { BottomNavigation } from '../components/BottomNavigation';

interface PromotionsScreenProps {
  onBack: () => void;
  activeTab: 'home' | 'results' | 'appointment' | 'promotions' | 'services';
  onTabChange: (tab: PromotionsScreenProps['activeTab']) => void;
}

export function PromotionsScreen({ onBack, activeTab, onTabChange }: PromotionsScreenProps) {
  return (
    <div className="min-h-screen bg-background pb-24">
      <TopAppBar
        title="Бонусы и акции"
        subtitle="Программа лояльности"
        onBack={onBack}
      />

      <main className="pt-20 px-4 pb-6 max-w-[390px] mx-auto space-y-4">
        <div className="bg-white rounded-[24px] p-5 border border-border">
          <h3 className="font-semibold text-[15px] text-navy-text mb-4">
            Мини-программа лояльности
          </h3>

          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-mint-bg rounded-[16px] p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
                  <Gift size={16} className="text-primary" />
                </div>
              </div>
              <div className="text-2xl font-bold text-primary mb-1">1 250 ₽</div>
              <div className="text-xs text-secondary-text">Бонусные рубли</div>
            </div>

            <div className="bg-lavender-bg rounded-[16px] p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 rounded-full bg-[#9333EA]/20 flex items-center justify-center">
                  <Award size={16} className="text-[#9333EA]" />
                </div>
              </div>
              <div className="text-2xl font-bold text-[#9333EA] mb-1">7%</div>
              <div className="text-xs text-secondary-text">Текущая скидка</div>
            </div>
          </div>

          <div className="bg-sky-bg rounded-[16px] p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-navy-text">До следующего уровня</span>
              <span className="text-sm font-semibold text-primary">10 000 ₽ из 25 000 ₽</span>
            </div>
            <div className="w-full h-2 bg-white rounded-full overflow-hidden">
              <div className="h-full bg-primary rounded-full" style={{ width: '40%' }}></div>
            </div>
            <p className="text-xs text-secondary-text mt-2">
              Чтобы получить скидку 10%, необходимо набрать еще 15 000 ₽
            </p>
          </div>

          <div className="mt-4 grid grid-cols-3 gap-3 text-center">
            <div>
              <div className="text-xl font-bold text-navy-text">7%</div>
              <div className="text-[11px] text-secondary-text mt-1">Сейчас</div>
            </div>
            <div>
              <div className="text-xl font-bold text-secondary-text">10%</div>
              <div className="text-[11px] text-secondary-text mt-1">Уровень 2</div>
            </div>
            <div>
              <div className="text-xl font-bold text-secondary-text">15%</div>
              <div className="text-[11px] text-secondary-text mt-1">Уровень 3</div>
            </div>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-[15px] text-navy-text">
              Акции и спецпредложения
            </h3>
            <div className="flex gap-1">
              <div className="w-2 h-2 rounded-full bg-primary"></div>
              <div className="w-2 h-2 rounded-full bg-gray-300"></div>
              <div className="w-2 h-2 rounded-full bg-gray-300"></div>
            </div>
          </div>

          <div className="space-y-3">
            <div className="bg-gradient-to-br from-sky-bg to-primary-light rounded-[20px] p-5 border border-border">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-full bg-white/60 flex items-center justify-center flex-shrink-0">
                  <TrendingUp size={24} className="text-primary" />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-[15px] text-navy-text mb-1">
                    Комплексное обследование
                  </h4>
                  <p className="text-sm text-secondary-text mb-2">
                    Скидка 20% на комплекс анализов "Здоровье сердца"
                  </p>
                  <div className="inline-block px-3 py-1 bg-white rounded-full">
                    <span className="text-xs font-semibold text-primary">До 30.05.2024</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-br from-lavender-bg to-[#F0EBFF] rounded-[20px] p-5 border border-border">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 rounded-full bg-white/60 flex items-center justify-center flex-shrink-0">
                  <Gift size={24} className="text-[#9333EA]" />
                </div>
                <div className="flex-1">
                  <h4 className="font-semibold text-[15px] text-navy-text mb-1">
                    Скидка 15% на прием невролога
                  </h4>
                  <p className="text-sm text-secondary-text mb-2">
                    Первичная консультация со скидкой для новых пациентов
                  </p>
                  <div className="inline-block px-3 py-1 bg-white rounded-full">
                    <span className="text-xs font-semibold text-[#9333EA]">Постоянная</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-[20px] p-5 border border-border">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h4 className="font-semibold text-[15px] text-navy-text mb-1">
                Персональные предложения
              </h4>
              <p className="text-sm text-secondary-text">
                Настройте уведомления о скидках и акциях
              </p>
            </div>
            <button className="ml-3 p-2 hover:bg-gray-100 rounded-full transition-colors">
              <Settings size={20} className="text-primary" />
            </button>
          </div>
        </div>
      </main>

      <BottomNavigation activeTab={activeTab} onTabChange={onTabChange} />
    </div>
  );
}
