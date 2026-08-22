import React, { useEffect } from 'react';
import { Card } from '../components/core/Card';
import { Badge } from '../components/core/Badge';
import { AgentAvatar } from '../components/trading/AgentAvatar';
import { ConfidenceMeter } from '../components/trading/ConfidenceMeter';
import type { AIAgent } from '../types';
import { ThumbsUp, ThumbsDown, Clock, ShieldCheck, Newspaper, BarChart3, RefreshCw } from 'lucide-react';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api-client';

export const AICommandPage: React.FC = () => {
  const { aiAgents, setAIAgents, refreshAgents, initializeAgents } = useAppStore();
  const [loading, setLoading] = React.useState(true);

  useEffect(() => {
    refreshAgents().finally(() => setLoading(false));
    const interval = setInterval(refreshAgents, 15000);
    return () => clearInterval(interval);
  }, []);

  const buyVotes = aiAgents.filter((a) => a.decision === 'BUY').length;
  const sellVotes = aiAgents.filter((a) => a.decision === 'SELL').length;
  const waitVotes = aiAgents.filter((a) => a.decision === 'WAIT').length;
  const avgConfidence = aiAgents.length > 0
    ? Math.round(aiAgents.reduce((s, a) => s + a.confidence, 0) / aiAgents.length)
    : 0;
  const mainDecision = buyVotes > sellVotes && buyVotes > waitVotes ? 'BUY'
    : sellVotes > buyVotes && sellVotes > waitVotes ? 'SELL' : 'WAIT';

  return (
    <div className="h-full grid grid-cols-[1fr_320px] grid-rows-[auto_1fr] gap-3 p-3 overflow-auto">
      <div className="col-span-2 bg-trading-surface border border-panel-border rounded-[var(--radius-lg)] p-4 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <div className={`w-14 h-14 rounded-full border-2 flex items-center justify-center shadow-[0_0_20px_rgba(0,200,83,0.25)] ${
              mainDecision === 'BUY' ? 'bg-profit/15 border-profit' :
              mainDecision === 'SELL' ? 'bg-loss/15 border-loss' : 'bg-warning/15 border-warning'
            }`}>
              {mainDecision === 'BUY' ? <ThumbsUp className="w-7 h-7 text-profit" /> :
               mainDecision === 'SELL' ? <ThumbsDown className="w-7 h-7 text-loss" /> :
               <Clock className="w-7 h-7 text-warning" />}
            </div>
            <div>
              <div className={`text-[24px] font-bold tracking-tight ${
                mainDecision === 'BUY' ? 'text-profit' : mainDecision === 'SELL' ? 'text-loss' : 'text-warning'
              }`}>{mainDecision}</div>
              <div className="text-[11px] text-text-muted">Consensus Decision · {aiAgents.length} agents</div>
            </div>
          </div>

          <div className="flex items-center gap-4 pl-6 border-l border-panel-border">
            <div className="flex flex-col items-center">
              <span data-mono className="text-[18px] font-bold text-profit">{buyVotes}</span>
              <span className="text-[9px] text-text-muted uppercase">Buy</span>
            </div>
            <div className="flex flex-col items-center">
              <span data-mono className="text-[18px] font-bold text-loss">{sellVotes}</span>
              <span className="text-[9px] text-text-muted uppercase">Sell</span>
            </div>
            <div className="flex flex-col items-center">
              <span data-mono className="text-[18px] font-bold text-text-secondary">{waitVotes}</span>
              <span className="text-[9px] text-text-muted uppercase">Wait</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ConfidenceMeter value={avgConfidence} label="Avg Confidence" size={110} />
          <button onClick={refreshAgents} className="p-1.5 text-text-muted hover:text-text-primary">
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-3 overflow-auto">
        {loading && aiAgents.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-text-muted text-sm">Loading agents...</div>
        ) : aiAgents.length === 0 ? (
          <div className="flex items-center justify-center h-32 text-text-muted text-sm border border-dashed border-panel-border rounded-lg">
            <button onClick={() => Promise.resolve().then(initializeAgents).then(() => setLoading(false))} className="text-accent-blue hover:underline text-xs">
              Initialize AI Crew
            </button>
          </div>
        ) : aiAgents.map((agent) => (
          <div key={agent.id} className="bg-trading-surface border border-panel-border rounded-[var(--radius-lg)] p-3 flex gap-3">
            <AgentAvatar agent={agent} size="lg" showLabel={false} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <div>
                  <span className="text-[12px] font-semibold text-text-primary">{agent.name}</span>
                  <span className="text-[10px] text-text-muted ml-2">{agent.role}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={agent.decision === 'BUY' ? 'profit' : agent.decision === 'SELL' ? 'loss' : 'neutral'} dot>
                    {agent.decision}
                  </Badge>
                  <span data-mono className="text-[11px] text-text-secondary">{agent.confidence}%</span>
                </div>
              </div>
              <p className="text-[11px] text-text-secondary leading-relaxed">{agent.reasoning || 'Awaiting analysis...'}</p>
              <div className="flex items-center gap-3 mt-2">
                <span className="text-[9px] text-text-muted flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {new Date(agent.lastUpdated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                <span className="text-[9px] text-text-muted">Score: {agent.performanceScore}/100</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-3 overflow-auto">
        <Card title="Risk Summary" action={<ShieldCheck className="w-3.5 h-3.5 text-warning" />}>
          <ul className="space-y-2 text-[11px]">
            <li className="flex justify-between"><span className="text-text-muted">Portfolio Exposure</span><span data-mono className="text-text-primary">--%</span></li>
            <li className="flex justify-between"><span className="text-text-muted">VaR (1D, 95%)</span><span data-mono className="text-warning">$--</span></li>
            <li className="flex justify-between"><span className="text-text-muted">Active Agents</span><span data-mono className="text-text-primary">{aiAgents.length}</span></li>
          </ul>
        </Card>

        <Card title="Technical Summary" action={<BarChart3 className="w-3.5 h-3.5 text-accent-cyan" />}>
          <ul className="space-y-2 text-[11px]">
            <li className="flex justify-between"><span className="text-text-muted">Status</span><Badge variant={loading ? 'warning' : 'profit'}>{loading ? 'Loading' : 'Active'}</Badge></li>
            <li className="flex justify-between"><span className="text-text-muted">Consensus</span><span data-mono className="text-text-primary">{aiAgents.length} agents</span></li>
          </ul>
        </Card>
      </div>
    </div>
  );
};
