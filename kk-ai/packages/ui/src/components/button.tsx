import React, { type ButtonHTMLAttributes, type ReactNode } from 'react';
import { cn } from '../lib/utils';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  loading?: boolean;
  children: ReactNode;
}

const variantClasses: Record<string, string> = {
  default:
    'bg-primary text-primary-foreground hover:bg-primary/90',
  secondary:
    'bg-secondary text-secondary-foreground hover:bg-secondary/80',
  outline:
    'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
  ghost:
    'hover:bg-accent hover:text-accent-foreground',
  danger:
    'bg-destructive text-destructive-foreground hover:bg-destructive/90',
};

const sizeClasses: Record<string, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-10 px-4 py-2',
  lg: 'h-11 px-8',
  icon: 'h-10 w-10',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'default',
      size = 'md',
      loading = false,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={cn(
          'inline-flex items-center justify-center whitespace-nowrap rounded-md font-medium',
          'ring-offset-background transition-colors focus-visible:outline-none',
          'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
          'disabled:pointer-events-none disabled:opacity-50',
          variantClasses[variant],
          sizeClasses[size],
          className
        )}
        {...props}
      >
        {loading && (
          <svg
            className="mr-2 h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        )}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
