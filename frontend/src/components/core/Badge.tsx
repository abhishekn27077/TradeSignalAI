import React from 'react';

/* ========================================================================== */
/* BADGE — Status / label badge for the trading UI                            */
/* ========================================================================== */

type BadgeVariant = 'profit' | 'loss' | 'warning' | 'info' | 'neutral' | 'accent';

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  dot?: boolean;
  className?: string;
}

const badgeStyles: Record<BadgeVariant, string> = {
  profit: 'bg-profit/15 text-profit border-profit/20',
  loss: 'bg-loss/10 text-loss border-loss/20',
  warning: 'bg-warning/10 text-warning border-warning/20',
  info: 'bg-info/10 text-info border-info/20',
  neutral: 'bg-trading-elevated text-text-secondary border-panel-border',
  accent: 'bg-accent-green/10 text-accent-green border-accent-green/20',
};

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  dot = false,
  children,
  className = '',
}) => {
  return (
    <span
      className={`
        inline-flex items-center gap-1.5
        px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider
        border rounded-full select-none
        ${badgeStyles[variant]}
        ${className}
      `}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            variant === 'profit' ? 'bg-profit' :
            variant === 'loss' ? 'bg-loss' :
            variant === 'warning' ? 'bg-warning' :
            variant === 'info' ? 'bg-info' :
            variant === 'accent' ? 'bg-accent-green' :
            'bg-text-muted'
          }`}
        />
      )}
      {children}
    </span>
  );
};
