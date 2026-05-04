import { InputHTMLAttributes, forwardRef, useState } from 'react';
import { Eye, EyeOff, User, Lock } from 'lucide-react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  icon?: 'user' | 'lock';
  error?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ icon, error, className = '', type, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = type === 'password';
    const inputType = isPassword && showPassword ? 'text' : type;

    const IconComponent = icon === 'user' ? User : icon === 'lock' ? Lock : null;

    return (
      <div className="relative">
        {IconComponent && (
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-secondary-text">
            <IconComponent size={20} />
          </div>
        )}

        <input
          ref={ref}
          type={inputType}
          className={`
            w-full h-[52px] px-4
            ${IconComponent ? 'pl-12' : ''}
            ${isPassword ? 'pr-12' : ''}
            bg-input-background border border-input-border rounded-[16px]
            text-navy-text placeholder:text-muted-text
            focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20
            transition-all
            ${error ? 'border-error focus:border-error focus:ring-error/20' : ''}
            ${className}
          `}
          {...props}
        />

        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-secondary-text hover:text-navy-text transition-colors"
          >
            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
          </button>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
