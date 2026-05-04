import { Camera, Calendar, Phone, Mail } from 'lucide-react';

interface ProfileCardProps {
  name: string;
  birthDate: string;
  phone: string;
  email: string;
  avatarUrl?: string;
}

export function ProfileCard({ name, birthDate, phone, email, avatarUrl }: ProfileCardProps) {
  return (
    <div className="bg-white rounded-[24px] p-5 shadow-sm border border-border">
      <div className="flex items-start gap-4">
        <div className="relative flex-shrink-0">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-light to-primary/20 flex items-center justify-center overflow-hidden">
            {avatarUrl ? (
              <img src={avatarUrl} alt={name} className="w-full h-full object-cover" />
            ) : (
              <span className="text-2xl font-semibold text-primary">
                {name.split(' ').map(n => n[0]).join('')}
              </span>
            )}
          </div>
          <button className="absolute bottom-0 right-0 w-6 h-6 bg-primary rounded-full flex items-center justify-center shadow-md">
            <Camera size={14} className="text-white" />
          </button>
        </div>

        <div className="flex-1 min-w-0">
          <h2 className="font-semibold text-[17px] text-navy-text">
            {name}
          </h2>

          <div className="mt-3 space-y-2">
            <div className="flex items-center gap-2 text-[14px]">
              <Calendar size={16} className="text-secondary-text flex-shrink-0" />
              <span className="text-secondary-text">{birthDate}</span>
            </div>

            <div className="flex items-center gap-2 text-[14px]">
              <Phone size={16} className="text-secondary-text flex-shrink-0" />
              <span className="text-navy-text">{phone}</span>
            </div>

            <div className="flex items-center gap-2 text-[14px]">
              <Mail size={16} className="text-secondary-text flex-shrink-0" />
              <span className="text-navy-text truncate">{email}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-divider">
        <div className="flex items-center gap-2 text-[13px] text-secondary-text">
          <div className="w-1 h-1 rounded-full bg-info"></div>
          <span>Нажмите на камеру для изменения фото профиля</span>
        </div>
      </div>
    </div>
  );
}
