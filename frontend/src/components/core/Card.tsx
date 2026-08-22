import React from 'react';

/* ========================================================================== */
/* CARD — Glass panel card for the trading terminal                           */
/* ========================================================================== */

interface CardProps {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  noPadding?: boolean;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  action,
  children,
  className = '',
  noPadding = false,
}) => {
  return (
    <div
      className={`
        bg-trading-surface border border-panel-border rounded-[var(--radius-lg)]
        shadow-[var(--shadow-panel)]
        flex flex-col h-full
        ${className}
      `}
    >
      {(title || action) && (
        <div className="flex items-center justify-between px-3 py-2 border-b border-panel-border min-h-[36px]">
          <div className="flex flex-col">
            {title && (
              <h3 className="text-[12px] font-semibold text-text-primary tracking-wide uppercase">
                {title}
              </h3>
            )}
            {subtitle && (
              <span className="text-[10px] text-text-muted">{subtitle}</span>
            )}
          </div>
          {action && <div className="flex items-center gap-1">{action}</div>}
        </div>
      )}
      <div className={`flex-1 overflow-auto ${noPadding ? '' : 'p-3'}`}>
        {children}
      </div>
    </div>
  );
};
