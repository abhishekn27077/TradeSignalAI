import React from 'react';
import type { AIAgent, AgentStatus } from '../../types';

/* ========================================================================== */
/* AGENT AVATAR — Glowing ring showing AI agent status                        */
/* ========================================================================== */

interface AgentAvatarProps {
  agent: AIAgent;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

const statusColors: Record<AgentStatus, string> = {
  thinking: 'border-accent-blue shadow-[0_0_8px_rgba(88,166,255,0.4)]',
  confident: 'border-profit shadow-[0_0_8px_rgba(0,200,83,0.4)]',
  waiting: 'border-text-muted',
  error: 'border-loss shadow-[0_0_8px_rgba(255,59,48,0.4)]',
};

const statusLabel: Record<AgentStatus, string> = {
  thinking: 'Analyzing',
  confident: 'Confident',
  waiting: 'Idle',
  error: 'Error',
};

const sizeMap = {
  sm: 'w-7 h-7 text-[10px]',
  md: 'w-9 h-9 text-[11px]',
  lg: 'w-12 h-12 text-[13px]',
};

export const AgentAvatar: React.FC<AgentAvatarProps> = ({
  agent,
  size = 'md',
  showLabel = true,
}) => {
  const initials = agent.name
    .split(' ')
    .map((w) => w[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="flex items-center gap-2">
      <div
        className={`
          ${sizeMap[size]}
          rounded-full border-2
          bg-trading-elevated
          flex items-center justify-center
          font-semibold text-text-primary
          transition-all duration-300
          ${statusColors[agent.status]}
          ${agent.status === 'thinking' ? 'animate-pulse' : ''}
        `}
        title={`${agent.name} — ${statusLabel[agent.status]}`}
      >
        {initials}
      </div>
      {showLabel && (
        <div className="flex flex-col">
          <span className="text-[11px] font-medium text-text-primary leading-tight">
            {agent.name}
          </span>
          <span className="text-[9px] text-text-muted leading-tight">
            {agent.role}
          </span>
        </div>
      )}
    </div>
  );
};
