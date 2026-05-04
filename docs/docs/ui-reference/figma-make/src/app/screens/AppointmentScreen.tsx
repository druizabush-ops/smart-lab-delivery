import { useState } from 'react';
import { Phone } from 'lucide-react';
import { TopAppBar } from '../components/TopAppBar';
import { BottomNavigation } from '../components/BottomNavigation';
import { SearchInput } from '../components/SearchInput';
import { DoctorCard } from '../components/DoctorCard';

interface AppointmentScreenProps {
  onBack: () => void;
  activeTab: 'home' | 'results' | 'appointment' | 'promotions' | 'services';
  onTabChange: (tab: AppointmentScreenProps['activeTab']) => void;
}

const mockDoctors = [
  {
    name: 'Иванова Анна Сергеевна',
    specialty: 'Терапевт',
    isAdultDoctor: true,
    hasOnlineBooking: true,
    availableSlots: ['09:00', '10:30', '12:00', '14:00']
  },
  {
    name: 'Петров Дмитрий Олегович',
    specialty: 'Кардиолог',
    isAdultDoctor: true,
    hasOnlineBooking: true,
    availableSlots: ['08:30', '11:00', '15:30', '17:00']
  },
  {
    name: 'Смирнова Екатерина Игоревна',
    specialty: 'Невролог',
    isAdultDoctor: true,
    hasOnlineBooking: true,
    availableSlots: ['09:30', '12:30', '14:30']
  },
  {
    name: 'Кузнецова Мария Павловна',
    specialty: 'Эндокринолог',
    isAdultDoctor: true,
    hasOnlineBooking: true,
    availableSlots: ['10:00', '13:00', '16:00', '18:00']
  }
];

export function AppointmentScreen({ onBack, activeTab, onTabChange }: AppointmentScreenProps) {
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="min-h-screen bg-background pb-24">
      <TopAppBar
        title="Запись на прием"
        subtitle="Выберите врача и удобное время"
        onBack={onBack}
        rightAction="filter"
      />

      <main className="pt-20 px-4 pb-6 max-w-[390px] mx-auto">
        <div className="mb-4">
          <SearchInput
            placeholder="Поиск по врачу или специальности"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onClear={() => setSearchQuery('')}
          />
        </div>

        <div className="space-y-3">
          {mockDoctors.map((doctor, idx) => (
            <DoctorCard
              key={idx}
              {...doctor}
              onClick={() => {}}
            />
          ))}
        </div>

        <div className="mt-6 bg-white rounded-[20px] p-5 border border-border">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-primary-light flex items-center justify-center flex-shrink-0">
              <Phone size={20} className="text-primary" />
            </div>
            <div className="flex-1">
              <p className="text-sm text-navy-text mb-1">
                Не нашли нужного врача?
              </p>
              <p className="text-xs text-secondary-text mb-2">
                Позвоните в контакт-центр
              </p>
              <a href="tel:+79991234567" className="text-base font-semibold text-primary">
                +7 (999) 123-45-67
              </a>
            </div>
          </div>
        </div>
      </main>

      <BottomNavigation activeTab={activeTab} onTabChange={onTabChange} />
    </div>
  );
}
