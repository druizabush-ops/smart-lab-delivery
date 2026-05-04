import { Send, Share2, Download } from 'lucide-react';
import { TopAppBar } from '../components/TopAppBar';
import { BottomNavigation } from '../components/BottomNavigation';

interface PDFViewerScreenProps {
  onBack: () => void;
  activeTab: 'home' | 'results' | 'appointment' | 'promotions' | 'services';
  onTabChange: (tab: PDFViewerScreenProps['activeTab']) => void;
}

export function PDFViewerScreen({ onBack, activeTab, onTabChange }: PDFViewerScreenProps) {
  return (
    <div className="min-h-screen bg-background pb-44">
      <TopAppBar
        title="Исследование №125487"
        subtitle="PDF документ"
        onBack={onBack}
      />

      <main className="pt-20 px-4 pb-6 max-w-[390px] mx-auto">
        <div className="bg-white rounded-[20px] p-4 border border-border shadow-lg">
          <div className="aspect-[3/4] bg-gray-50 rounded-lg overflow-hidden border border-gray-200">
            <div className="w-full h-full bg-white p-6 text-[10px] overflow-auto">
              <div className="mb-4 flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 bg-primary rounded-lg"></div>
                    <div>
                      <div className="font-bold text-primary">ГЕМОТЕСТ</div>
                      <div className="text-[8px] text-gray-500">Медицинская лаборатория</div>
                    </div>
                  </div>
                </div>
                <div className="text-right text-[8px] text-gray-500">
                  <div>№ 125487</div>
                  <div>от 20.04.2024</div>
                </div>
              </div>

              <div className="border-t border-gray-200 pt-3 mb-3">
                <div className="text-[9px] font-semibold mb-2">Пациент:</div>
                <div className="text-[8px] text-gray-600 space-y-0.5">
                  <div>Иванов Иван Иванович</div>
                  <div>Дата рождения: 15.04.1988 (38 лет)</div>
                  <div>Пол: Мужской</div>
                </div>
              </div>

              <div className="border-t border-gray-200 pt-3 mb-3">
                <div className="text-[9px] font-semibold mb-2">БИОХИМИЧЕСКИЕ ИССЛЕДОВАНИЯ КРОВИ</div>
                <table className="w-full text-[8px]">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-1 font-medium">Показатель</th>
                      <th className="text-left py-1 font-medium">Результат</th>
                      <th className="text-left py-1 font-medium">Ед. изм.</th>
                      <th className="text-left py-1 font-medium">Референс</th>
                    </tr>
                  </thead>
                  <tbody className="text-gray-600">
                    <tr className="border-b border-gray-100">
                      <td className="py-1.5">Холестерин общий</td>
                      <td className="py-1.5">4.2</td>
                      <td className="py-1.5">ммоль/л</td>
                      <td className="py-1.5">3.5 - 5.2</td>
                    </tr>
                    <tr className="border-b border-gray-100">
                      <td className="py-1.5">Глюкоза</td>
                      <td className="py-1.5">5.383</td>
                      <td className="py-1.5">ммоль/л</td>
                      <td className="py-1.5">3.88 - 5.83</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="border-t border-gray-200 pt-3">
                <div className="text-[8px] text-gray-400 italic">
                  Результаты исследований не являются диагнозом. Интерпретация результатов должна проводиться лечащим врачом.
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-gray-200 flex justify-between items-end text-[8px] text-gray-500">
                <div>
                  <div>Врач-лаборант:</div>
                  <div className="mt-1">_____________ Петрова А.С.</div>
                </div>
                <div className="text-right">
                  <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40'%3E%3Ccircle cx='20' cy='20' r='18' fill='%2316B1AC' opacity='0.1'/%3E%3Ctext x='20' y='25' text-anchor='middle' fill='%2316B1AC' font-size='10' font-family='monospace'%3EПЕЧАТЬ%3C/text%3E%3C/svg%3E" alt="stamp" className="w-10 h-10" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="fixed bottom-20 left-0 right-0 bg-white border-t border-border py-3 px-4 ">
          <div className="max-w-[390px] mx-auto flex gap-2">
            <button className="flex-1 h-12 flex items-center justify-center gap-2 bg-primary-light text-primary rounded-[16px] font-medium transition-all active:scale-[0.98]">
              <Send size={18} />
              <span className="text-sm">Отправить в MAX</span>
            </button>

            <button className="h-12 px-4 flex items-center justify-center bg-gray-100 text-navy-text rounded-[16px] transition-all active:scale-[0.98]">
              <Share2 size={18} />
            </button>

            <button className="h-12 px-4 flex items-center justify-center bg-gray-100 text-navy-text rounded-[16px] transition-all active:scale-[0.98]">
              <Download size={18} />
            </button>
          </div>
        </div>
      </main>

      <BottomNavigation activeTab={activeTab} onTabChange={onTabChange} />
    </div>
  );
}
