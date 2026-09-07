import React, { useEffect, useState } from 'react';
import {
  LayoutDashboard, Zap, Clock, TrendingUp, Archive, Briefcase, BookOpen,
  Settings, Activity, ChevronLeft, ChevronRight, ChevronDown, ChevronUp,
  Lock, Unlock, PieChart, FlaskConical, PlayCircle, BarChart, GitMerge,
  Trophy, Grid, Brain, Search, Shield, ShieldAlert, Layers, HardDrive, Download,
  Award, Target, CandlestickChart, Crosshair, Newspaper, Database, Scale,
  CalendarDays, Sun, Calendar, CheckSquare, BarChart2, Radio,
} from 'lucide-react';
import { useAppStore } from '../../store/useAppStore';

/* ========================================================================== */
/* SIDEBAR — Professional Trading Terminal Navigation                         */
/* ========================================================================== */

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  children?: NavItem[];
}

/* ── Main Navigation (visible to all users) ─────────────────────────────── */
const mainNav: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: <LayoutDashboard className="w-4 h-4" /> },
  {
    id: 'signals-group', label: 'Signals', icon: <Zap className="w-4 h-4" />,
    children: [
      { id: 'trade-terminal', label: 'Trade Signal Terminal (P69A)', icon: <Zap className="w-3.5 h-3.5 text-cyan-400" /> },
      { id: 'signal-feed-schedule', label: 'Signal Feed & Schedule (P64)', icon: <Radio className="w-3.5 h-3.5" /> },
      { id: 'todays-signals', label: "Today's Signals", icon: <Clock className="w-3.5 h-3.5" /> },
      { id: 'market-structure', label: 'Smart Money & Structure (P51)', icon: <Layers className="w-3.5 h-3.5" /> },
      { id: 'h4-forecasts-new', label: 'H4 Forecasts', icon: <Clock className="w-3.5 h-3.5" /> },
      { id: 'swing-signals', label: 'Swing Signals', icon: <TrendingUp className="w-3.5 h-3.5" /> },
      { id: 'signal-history', label: 'Signal History', icon: <Archive className="w-3.5 h-3.5" /> },
    ],
  },
  {
    id: 'forecasts-group', label: 'Forecasts', icon: <Sun className="w-4 h-4" />,
    children: [
      { id: 'daily-command', label: 'Daily Command', icon: <Radio className="w-3.5 h-3.5" /> },
      { id: 'live-edge', label: 'Live Edge Evidence', icon: <Scale className="w-3.5 h-3.5" /> },
      { id: 'tomorrow-forecast', label: 'Tomorrow Forecast', icon: <Sun className="w-3.5 h-3.5" /> },
      { id: 'phase43-shadow', label: 'Shadow Validation', icon: <Shield className="w-3.5 h-3.5" /> },
      { id: 'reality-evidence', label: 'Reality & Evidence', icon: <Scale className="w-3.5 h-3.5" /> },
      { id: 'prediction-lab', label: 'Prediction Lab', icon: <FlaskConical className="w-3.5 h-3.5" /> },
      { id: 'prediction-ledger', label: 'Prediction Ledger', icon: <CheckSquare className="w-3.5 h-3.5" /> },
      { id: 'economic-calendar', label: 'Economic Calendar', icon: <CalendarDays className="w-3.5 h-3.5" /> },
      { id: 'news-intelligence', label: 'News Intelligence', icon: <Newspaper className="w-3.5 h-3.5" /> },
    ],
  },
  { id: 'portfolio', label: 'Portfolio', icon: <Briefcase className="w-4 h-4" /> },
  { id: 'journal', label: 'Journal', icon: <BookOpen className="w-4 h-4" /> },
  { id: 'system-health', label: 'System Health', icon: <Activity className="w-4 h-4" /> },
  { id: 'config-center', label: 'Settings', icon: <Settings className="w-4 h-4" /> },
];

/* ── Admin Navigation (hidden by default) ───────────────────────────────── */
interface AdminSection { label: string; items: NavItem[]; }

const adminSections: AdminSection[] = [
  {
    label: 'Research',
    items: [
      { id: 'ai-research-dashboard', label: 'Research Dashboard', icon: <PieChart className="w-3.5 h-3.5" /> },
      { id: 'enterprise-backtest', label: 'Backtesting Lab', icon: <FlaskConical className="w-3.5 h-3.5" /> },
      { id: 'historical-replay', label: 'Replay Engine', icon: <PlayCircle className="w-3.5 h-3.5" /> },
      { id: 'model-comparison', label: 'Model Comparison', icon: <BarChart className="w-3.5 h-3.5" /> },
      { id: 'hyperparameter-lab', label: 'Hyperparameter Lab', icon: <GitMerge className="w-3.5 h-3.5" /> },
      { id: 'model-leaderboard', label: 'Leaderboard', icon: <Trophy className="w-3.5 h-3.5" /> },
    ],
  },
  {
    label: 'Strategy Lab',
    items: [
      { id: 'strategy-lab', label: 'Strategy Lab', icon: <FlaskConical className="w-3.5 h-3.5" /> },
      { id: 'strategy-builder', label: 'Strategy Builder', icon: <Grid className="w-3.5 h-3.5" /> },
      { id: 'strategy-library', label: 'Strategy Library', icon: <Archive className="w-3.5 h-3.5" /> },
      { id: 'experiment-manager', label: 'Experiment Manager', icon: <PlayCircle className="w-3.5 h-3.5" /> },
      { id: 'research-notebook', label: 'Research Notebook', icon: <BookOpen className="w-3.5 h-3.5" /> },
      { id: 'feature-importance', label: 'Feature Importance', icon: <BarChart className="w-3.5 h-3.5" /> },
      { id: 'benchmark-center', label: 'Benchmark Center', icon: <Trophy className="w-3.5 h-3.5" /> },
      { id: 'ai-recommendations', label: 'AI Recommendations', icon: <Brain className="w-3.5 h-3.5" /> },
    ],
  },
  {
    label: 'Market Intelligence',
    items: [
      { id: 'market-structure', label: 'Phase 51 Intelligence', icon: <Layers className="w-3.5 h-3.5" /> },
      { id: 'market-command', label: 'Command Center', icon: <LayoutDashboard className="w-3.5 h-3.5" /> },
      { id: 'currency-strength', label: 'Currency Strength', icon: <BarChart2 className="w-3.5 h-3.5" /> },
      { id: 'correlation-matrix', label: 'Correlation Matrix', icon: <Grid className="w-3.5 h-3.5" /> },
      { id: 'portfolio-intel', label: 'Portfolio Intelligence', icon: <PieChart className="w-3.5 h-3.5" /> },
      { id: 'capital-allocation', label: 'Capital Allocation', icon: <Briefcase className="w-3.5 h-3.5" /> },
      { id: 'exposure-monitor', label: 'Exposure Monitor', icon: <ShieldAlert className="w-3.5 h-3.5" /> },
      { id: 'ai-portfolio-manager', label: 'AI Portfolio Mgr', icon: <Brain className="w-3.5 h-3.5" /> },
      { id: 'sector-rotation', label: 'Sector Rotation', icon: <TrendingUp className="w-3.5 h-3.5" /> },
      { id: 'opportunity-explorer', label: 'Opportunity Explorer', icon: <Search className="w-3.5 h-3.5" /> },
      { id: 'global-risk', label: 'Global Risk', icon: <Activity className="w-3.5 h-3.5" /> },
    ],
  },
  {
    label: 'Data Foundation',
    items: [
      { id: 'market-database', label: 'Market DB', icon: <HardDrive className="w-3.5 h-3.5" /> },
      { id: 'data-manager', label: 'Data Manager', icon: <Download className="w-3.5 h-3.5" /> },
      { id: 'feature-store', label: 'Feature Store', icon: <Layers className="w-3.5 h-3.5" /> },
    ],
  },
  {
    label: 'Enterprise',
    items: [
      { id: 'qualification', label: 'Qualification', icon: <Award className="w-3.5 h-3.5" /> },
      { id: 'audit-log', label: 'Audit Log', icon: <ShieldAlert className="w-3.5 h-3.5" /> },
      { id: 'config-center', label: 'Configuration', icon: <Settings className="w-3.5 h-3.5" /> },
      { id: 'plugin-manager', label: 'Plugins', icon: <Layers className="w-3.5 h-3.5" /> },
    ],
  },
  {
    label: 'Legacy',
    items: [
      { id: 'terminal', label: 'Terminal', icon: <CandlestickChart className="w-3.5 h-3.5" /> },
      { id: 'ai-command', label: 'AI Command', icon: <Brain className="w-3.5 h-3.5" /> },
      { id: 'strategies', label: 'Strategies', icon: <Crosshair className="w-3.5 h-3.5" /> },
      { id: 'signals', label: 'Signals (Legacy)', icon: <Zap className="w-3.5 h-3.5" /> },
      { id: 'news', label: 'News', icon: <Newspaper className="w-3.5 h-3.5" /> },
      { id: 'risk', label: 'Risk', icon: <ShieldAlert className="w-3.5 h-3.5" /> },
      { id: 'execution', label: 'Execution', icon: <Activity className="w-3.5 h-3.5" /> },
      { id: 'memory', label: 'Memory', icon: <Database className="w-3.5 h-3.5" /> },
      { id: 'decision-dashboard', label: 'Decision Board', icon: <Award className="w-3.5 h-3.5" /> },
      { id: 'decision-history', label: 'Decision History', icon: <Archive className="w-3.5 h-3.5" /> },
      { id: 'forecast-dashboard', label: 'Forecast Dash', icon: <LayoutDashboard className="w-3.5 h-3.5" /> },
      { id: 'prediction-center', label: 'Prediction Center', icon: <Target className="w-3.5 h-3.5" /> },
      { id: 'model-performance', label: 'Model Performance', icon: <TrendingUp className="w-3.5 h-3.5" /> },
      { id: 'forecast-validation', label: 'Validation', icon: <CheckSquare className="w-3.5 h-3.5" /> },
      { id: 'forecast-archive', label: 'Archive', icon: <Archive className="w-3.5 h-3.5" /> },
      { id: 'trade-schedule', label: 'Schedule Center', icon: <CalendarDays className="w-3.5 h-3.5" /> },
      { id: 'market-heatmap', label: 'Heatmap', icon: <Grid className="w-3.5 h-3.5" /> },
      { id: 'daily-outlook', label: 'Daily Outlook', icon: <Sun className="w-3.5 h-3.5" /> },
      { id: 'weekly-outlook', label: 'Weekly Outlook', icon: <Calendar className="w-3.5 h-3.5" /> },
    ],
  },
];

export const Sidebar: React.FC = () => {
  const collapsed = useAppStore((s) => s.sidebarCollapsed);
  const activePage = useAppStore((s) => s.activePage);
  const adminMode = useAppStore((s) => s.adminMode);
  const toggleSidebar = useAppStore((s) => s.toggleSidebar);
  const setActivePage = useAppStore((s) => s.setActivePage);
  const toggleAdminMode = useAppStore((s) => s.toggleAdminMode);

  const [openGroups, setOpenGroups] = useState<Set<string>>(new Set(['signals-group']));
  const [openAdminSections, setOpenAdminSections] = useState<Set<string>>(new Set());

  // Ctrl+Shift+A to toggle admin mode
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'A') {
        e.preventDefault();
        toggleAdminMode();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [toggleAdminMode]);

  const toggleGroup = (id: string) => {
    setOpenGroups(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleAdminSection = (label: string) => {
    setOpenAdminSections(prev => {
      const next = new Set(prev);
      if (next.has(label)) next.delete(label); else next.add(label);
      return next;
    });
  };

  const NavButton: React.FC<{ item: NavItem; indent?: boolean }> = ({ item, indent }) => (
    <button
      onClick={() => item.children ? toggleGroup(item.id) : setActivePage(item.id)}
      className={`
        w-full flex items-center gap-2.5 rounded-[var(--radius-md)]
        transition-all duration-150 cursor-pointer
        ${collapsed ? 'justify-center px-0 py-2' : `${indent ? 'pl-7' : 'px-2.5'} pr-2.5 py-1.5`}
        ${activePage === item.id
          ? 'bg-accent-blue/12 text-accent-blue border border-accent-blue/20'
          : 'text-text-secondary hover:bg-trading-hover hover:text-text-primary border border-transparent'
        }
      `}
      title={collapsed ? item.label : undefined}
      aria-label={item.label}
    >
      {item.icon}
      {!collapsed && (
        <>
          <span className="text-[11px] font-medium flex-1 text-left">{item.label}</span>
          {item.children && (
            openGroups.has(item.id)
              ? <ChevronUp className="w-3 h-3 text-text-muted" />
              : <ChevronDown className="w-3 h-3 text-text-muted" />
          )}
        </>
      )}
    </button>
  );

  return (
    <aside
      className={`
        h-full bg-trading-surface border-r border-panel-border
        flex flex-col justify-between
        transition-all duration-200 ease-out
        z-[var(--z-sidebar)]
        ${collapsed ? 'w-12' : 'w-52'}
      `}
    >
      {/* Main Navigation */}
      <nav className="flex flex-col gap-0.5 p-1.5 overflow-y-auto scrollbar-none">
        {!collapsed && (
          <span className="text-[9px] font-semibold text-text-muted uppercase tracking-widest px-2 pt-2 pb-1">
            Trading
          </span>
        )}

        {mainNav.map((item) => (
          <React.Fragment key={item.id}>
            <NavButton item={item} />

            {/* Sub-menu for Signals */}
            {item.children && !collapsed && (
              <div className={`sidebar-submenu ${openGroups.has(item.id) ? 'sidebar-submenu-open' : ''}`}>
                <div className="flex flex-col gap-0.5 py-0.5">
                  {item.children.map((child) => (
                    <NavButton key={child.id} item={child} indent />
                  ))}
                </div>
              </div>
            )}
          </React.Fragment>
        ))}

        {/* ── Admin Section ─────────────────────────────────────────── */}
        {adminMode && !collapsed && (
          <>
            <div className="h-px bg-panel-border my-3" />
            <span className="text-[9px] font-semibold text-accent-gold/70 uppercase tracking-widest px-2 pb-1 flex items-center gap-1">
              <Unlock className="w-3 h-3" /> Admin
            </span>

            {adminSections.map((section) => (
              <React.Fragment key={section.label}>
                <button
                  onClick={() => toggleAdminSection(section.label)}
                  className="w-full flex items-center justify-between px-2.5 py-1.5 text-[10px] font-semibold text-text-muted uppercase tracking-wider hover:text-text-secondary transition-colors cursor-pointer"
                >
                  {section.label}
                  {openAdminSections.has(section.label)
                    ? <ChevronUp className="w-3 h-3" />
                    : <ChevronDown className="w-3 h-3" />
                  }
                </button>
                {openAdminSections.has(section.label) && (
                  <div className="flex flex-col gap-0.5 pb-1">
                    {section.items.map((item) => (
                      <NavButton key={item.id} item={item} indent />
                    ))}
                  </div>
                )}
              </React.Fragment>
            ))}
          </>
        )}

        {adminMode && collapsed && (
          <>
            <div className="h-2" />
            {adminSections.flatMap(s => s.items).map(item => (
              <NavButton key={item.id} item={item} />
            ))}
          </>
        )}
      </nav>

      {/* Footer: Admin Toggle + Collapse */}
      <div className="p-1.5 border-t border-panel-border space-y-1">
        {/* Admin Toggle */}
        <button
          onClick={toggleAdminMode}
          className={`
            w-full flex items-center justify-center gap-2 py-1.5
            text-[10px] font-medium
            transition-colors duration-150 cursor-pointer
            rounded-[var(--radius-md)] hover:bg-trading-hover
            ${adminMode ? 'text-accent-gold' : 'text-text-muted hover:text-text-secondary'}
          `}
          title={adminMode ? 'Hide Admin (Ctrl+Shift+A)' : 'Show Admin (Ctrl+Shift+A)'}
        >
          {adminMode ? <Unlock className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
          {!collapsed && (adminMode ? 'Admin ON' : 'Admin')}
        </button>

        {/* Collapse Toggle */}
        <button
          onClick={toggleSidebar}
          className="
            w-full flex items-center justify-center py-1.5
            text-text-muted hover:text-text-primary
            transition-colors duration-150 cursor-pointer
            rounded-[var(--radius-md)] hover:bg-trading-hover
          "
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
};
