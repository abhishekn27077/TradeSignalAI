import React from 'react';

/* ========================================================================== */
/* CONFIDENCE METER — Visual arc gauge for AI confidence                      */
/* ========================================================================== */

interface ConfidenceMeterProps {
  value: number; // 0–100
  label?: string;
  size?: number;
}

export const ConfidenceMeter: React.FC<ConfidenceMeterProps> = ({
  value,
  label = 'Confidence',
  size = 100,
}) => {
  const clampedValue = Math.max(0, Math.min(100, value));
  const radius = (size - 12) / 2;
  const circumference = Math.PI * radius; // semicircle
  const offset = circumference - (clampedValue / 100) * circumference;

  const color =
    clampedValue >= 75 ? 'var(--color-profit)' :
    clampedValue >= 50 ? 'var(--color-warning)' :
    'var(--color-loss)';

  return (
    <div className="flex flex-col items-center gap-1">
      <svg
        width={size}
        height={size / 2 + 10}
        viewBox={`0 0 ${size} ${size / 2 + 10}`}
        className="overflow-visible"
      >
        {/* Track */}
        <path
          d={`M 6 ${size / 2} A ${radius} ${radius} 0 0 1 ${size - 6} ${size / 2}`}
          fill="none"
          stroke="var(--color-panel-border)"
          strokeWidth="6"
          strokeLinecap="round"
        />
        {/* Value arc */}
        <path
          d={`M 6 ${size / 2} A ${radius} ${radius} 0 0 1 ${size - 6} ${size / 2}`}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500 ease-out"
          style={{ filter: `drop-shadow(0 0 6px ${color})` }}
        />
        {/* Value text */}
        <text
          x={size / 2}
          y={size / 2 - 4}
          textAnchor="middle"
          fill="var(--color-text-primary)"
          fontSize="18"
          fontWeight="600"
          fontFamily="var(--font-mono)"
        >
          {clampedValue}%
        </text>
      </svg>
      <span className="text-[10px] text-text-muted uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
};
