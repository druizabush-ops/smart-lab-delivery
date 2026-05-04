import { Search, X } from 'lucide-react';
import { InputHTMLAttributes, forwardRef } from 'react';

interface SearchInputProps extends InputHTMLAttributes<HTMLInputElement> {
  onClear?: () => void;
}

export const SearchInput = forwardRef<HTMLInputElement, SearchInputProps>(
  ({ onClear, value, className = '', ...props }, ref) => {
    return (
      <div className="relative">
        <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-secondary-text" />

        <input
          ref={ref}
          type="text"
          value={value}
          className={`
            w-full h-[48px] pl-12 pr-12
            bg-input-background border border-input-border rounded-[16px]
            text-navy-text placeholder:text-muted-text
            focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20
            transition-all
            ${className}
          `}
          {...props}
        />

        {value && onClear && (
          <button
            type="button"
            onClick={onClear}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-secondary-text hover:text-navy-text transition-colors"
          >
            <X size={20} />
          </button>
        )}
      </div>
    );
  }
);

SearchInput.displayName = 'SearchInput';
