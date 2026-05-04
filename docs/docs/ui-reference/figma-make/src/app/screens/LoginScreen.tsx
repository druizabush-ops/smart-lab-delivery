import { useState } from 'react';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { Phone } from 'lucide-react';

interface LoginScreenProps {
  onLogin: () => void;
}

export function LoginScreen({ onLogin }: LoginScreenProps) {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setError('');

    if (!login || !password) {
      setError('Заполните все поля');
      return;
    }

    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      onLogin();
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-light via-white to-sky-bg flex flex-col items-center justify-center p-6">
      <div className="w-full max-w-[390px]">
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-3">
            <div className="w-12 h-12 rounded-2xl bg-primary flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="none" className="w-7 h-7">
                <path d="M12 2L4 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-8-5z" fill="white" />
                <path d="M12 11a3 3 0 100-6 3 3 0 000 6zM12 12.5c-3.31 0-6 1.79-6 4v1.5h12V16.5c0-2.21-2.69-4-6-4z" fill="#16B1AC" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-primary">СМАРТ</h1>
          </div>
          <p className="text-sm text-secondary-text">Медицинский центр</p>
        </div>

        <div className="bg-white rounded-[28px] p-6 shadow-lg border border-border">
          <h2 className="text-xl font-semibold text-navy-text mb-2">
            Вход в систему
          </h2>
          <p className="text-sm text-secondary-text mb-6">
            Добро пожаловать в мини приложение медицинского центра СМАРТ
          </p>

          <div className="space-y-4 mb-6">
            <Input
              icon="user"
              type="text"
              placeholder="Логин"
              value={login}
              onChange={(e) => setLogin(e.target.value)}
              error={!!error}
            />

            <Input
              icon="lock"
              type="password"
              placeholder="Пароль"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={!!error}
            />

            {error && (
              <p className="text-sm text-error">{error}</p>
            )}
          </div>

          <Button
            variant="primary"
            size="large"
            className="w-full mb-4"
            onClick={handleLogin}
            loading={loading}
          >
            Войти
          </Button>

          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 h-px bg-divider"></div>
            <span className="text-sm text-muted-text">или</span>
            <div className="flex-1 h-px bg-divider"></div>
          </div>

          <Button
            variant="outline"
            size="large"
            className="w-full"
          >
            Зарегистрироваться
          </Button>
        </div>

        <div className="mt-6 bg-white rounded-[24px] p-5 shadow-sm border border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary-light flex items-center justify-center flex-shrink-0">
              <Phone size={20} className="text-primary" />
            </div>
            <div className="flex-1">
              <p className="text-xs text-secondary-text">Нужна помощь?</p>
              <a href="tel:+79991234567" className="text-base font-semibold text-primary">
                +7 (999) 123-45-67
              </a>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-muted-text mt-6">
          © 2024 Медицинский центр СМАРТ
        </p>
      </div>
    </div>
  );
}
