import React from 'react';

/* ========================================================================== */
/* BUTTON — Premium trading terminal button                                   */
/* ========================================================================== */

type ButtonVariant = 'primary' | 'danger' | 'ghost' | 'buy' | 'sell';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary:
    'bg-accent-blue/15 text-accent-blue border-accent-blue/30 hover:bg-accent-blue/25 hover:border-accent-blue/50',
  danger:
    'bg-loss/10 text-loss border-loss/30 hover:bg-loss/20 hover:border-loss/50',
  ghost:
    'bg-transparent text-text-secondary border-transparent hover:bg-trading-hover hover:text-text-primary',
  buy:
    'bg-profit/15 text-profit border-profit/30 hover:bg-profit/25 font-semibold',
  sell:
    'bg-loss/15 text-loss border-loss/30 hover:bg-loss/25 font-semibold',
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-2.5 py-1 text-[11px] gap-1',
  md: 'px-3.5 py-1.5 text-[12px] gap-1.5',
  lg: 'px-5 py-2.5 text-[13px] gap-2',
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  children,
  disabled,
  className = '',
  ...props
}) => {
  return (
    <button
      className={`
        inline-flex items-center justify-center
        border rounded-[var(--radius-md)]
        font-medium cursor-pointer select-none
        transition-all duration-200 ease-out
        focus:outline-none focus:ring-1 focus:ring-accent-blue/50
        disabled:opacity-40 disabled:cursor-not-allowed
        ${variantStyles[variant]}
        ${sizeStyles[size]}
        ${className}
      `}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : icon ? (
        <span className="w-3.5 h-3.5 flex-shrink-0">{icon}</span>
      ) : null}
      {children}
    </button>
  );
};
