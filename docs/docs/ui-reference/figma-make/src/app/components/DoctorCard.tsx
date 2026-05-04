import { ChevronRight, Heart, Users, Video } from 'lucide-react';
import { useState } from 'react';

interface DoctorCardProps {
  name: string;
  specialty: string;
  isAdultDoctor?: boolean;
  isKidsDoctor?: boolean;
  hasOnlineBooking?: boolean;
  availableSlots?: string[];
  photoUrl?: string;
  onClick: () => void;
}

export function DoctorCard({
  name,
  specialty,
  isAdultDoctor = true,
  isKidsDoctor = false,
  hasOnlineBooking = true,
  availableSlots = [],
  photoUrl,
  onClick
}: DoctorCardProps) {
  const [isFavorite, setIsFavorite] = useState(false);

  return (
    <div className="bg-white rounded-[20px] border border-border p-4">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0">
          <div className="w-16 h-16 rounded-full overflow-hidden bg-gradient-to-br from-sky-bg to-primary-light">
            {photoUrl ? (
              <img src={photoUrl} alt={name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-primary font-semibold text-lg">
                {name.split(' ').map(n => n[0]).join('')}
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-[15px] text-navy-text leading-tight">
            {name}
          </h3>
          <p className="text-[13px] text-secondary-text mt-1">
            {specialty}
          </p>

          <div className="flex items-center gap-3 mt-2">
            {isAdultDoctor && (
              <div className="flex items-center gap-1 text-[12px] text-secondary-text">
                <Users size={14} />
                <span>Взрослый</span>
              </div>
            )}
            {isKidsDoctor && (
              <div className="flex items-center gap-1 text-[12px] text-secondary-text">
                <Users size={14} />
                <span>Детский</span>
              </div>
            )}
            {hasOnlineBooking && (
              <div className="flex items-center gap-1 text-[12px] text-primary">
                <Video size={14} />
                <span>Онлайн</span>
              </div>
            )}
          </div>

          {availableSlots.length > 0 && (
            <div className="mt-3">
              <p className="text-[12px] text-secondary-text mb-2">Запись на {new Date().toLocaleDateString('ru')}</p>
              <div className="flex flex-wrap gap-2">
                {availableSlots.slice(0, 4).map((slot, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 bg-primary-light text-primary rounded-lg text-[12px] font-medium"
                  >
                    {slot}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-col items-center gap-3">
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsFavorite(!isFavorite);
            }}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <Heart
              size={20}
              className={isFavorite ? 'fill-error text-error' : 'text-secondary-text'}
            />
          </button>

          <button
            onClick={onClick}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <ChevronRight size={20} className="text-secondary-text" />
          </button>
        </div>
      </div>
    </div>
  );
}
