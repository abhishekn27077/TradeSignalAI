import React from 'react';

/* ========================================================================== */
/* KPI CARD — Large metric display for portfolio dashboard                    */
/* ========================================================================== */

interface KPICardProps {
  label: string;
  value: string;
  change?: number;
  icon?: React.ReactNode;
  className?: string;
}

export const KPICard: React.FC<KPICardProps> = ({
  label,
  value,
  change,
  icon,
  className = '',
}) => {
  const isPositive = change !== undefined && change >= 0;

  return (
    <div
      className={`
        bg-trading-surface border border-panel-border rounded-[var(--radius-lg)]
        p-4 flex flex-col gap-2 relative overflow-hidden
        ${className}
      `}
    >
      {/* Subtle glow behind the value */}
      {change !== undefined && (
        <div
          className={`absolute top-0 right-0 w-24 h-24 rounded-full blur-3xl opacity-20 ${
            isPositive ? 'bg-profit' : 'bg-loss'
          }`}
        />
      )}

      <div className="flex items-center justify-between relative z-10">
        <span className="text-[11px] font-medium text-text-muted uppercase tracking-wider">
          {label}
        </span>
        {icon && (
          <span className="w-4 h-4 text-text-muted">{icon}</span>
        )}
      </div>

      <span data-mono className="text-[22px] font-semibold text-text-primary relative z-10 tracking-tight">
        {value}
      </span>

      {change !== undefined && (
        <span
          data-mono
          className={`text-[12px] font-medium ${
            isPositive ? 'text-profit' : 'text-loss'
          }`}
        >
          {isPositive ? '+' : ''}{change.toFixed(2)}%
        </span>
      )}
    </div>
  );
};
