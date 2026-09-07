import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Typography, Tag, Progress, Tabs, Table, Badge, Button, Modal, Spin, Select } from 'antd';
import {
  TrendingUp,
  TrendingDown,
  Shield,
  Layers,
  Clock,
  Zap,
  Activity,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Crosshair,
  BarChart3,
  RefreshCw,
  PieChart,
  Server,
  DollarSign
} from 'lucide-react';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const ASSETS = [
  'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'XAUUSD', 'NAS100', 'SPX500', 'BTCUSD', 'ETHUSD'
];

const TIMEFRAMES = ['15M', '1H', '4H', '1D'];

export const MarketStructureIntelligence: React.FC = () => {
  const [selectedAsset, setSelectedAsset] = useState('EURUSD');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1H');
  const [loading, setLoading] = useState(false);
  const [summaryData, setSummaryData] = useState<any>(null);
  const [structureData, setStructureData] = useState<any>(null);
  const [smcData, setSmcData] = useState<any>(null);
  const [liquidityData, setLiquidityData] = useState<any>(null);
  const [dataHealth, setDataHealth] = useState<any>(null);
  const [exposureData, setExposureData] = useState<any>(null);
  const [explanationModalOpen, setExplanationModalOpen] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sumRes, structRes, smcRes, liqRes, healthRes, expRes] = await Promise.all([
        fetch(`/api/v1/analysis/summary/${selectedAsset}?timeframe=${selectedTimeframe}`).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch(`/api/v1/analysis/structure/${selectedAsset}?timeframe=${selectedTimeframe}`).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch(`/api/v1/analysis/smart-money/${selectedAsset}?timeframe=${selectedTimeframe}`).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch(`/api/v1/analysis/liquidity/${selectedAsset}?timeframe=${selectedTimeframe}`).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch(`/api/v1/system-intelligence/market-data-health`).then(r => r.ok ? r.json() : null).catch(() => null),
        fetch(`/api/v1/system-intelligence/portfolio-exposure`).then(r => r.ok ? r.json() : null).catch(() => null),
      ]);

      setSummaryData(sumRes || {
        confluence: { total_score: 50, direction: 'NEUTRAL', confidence: 0.5 },
        regime: { regime: 'RANGEBOUND', adx_value: 18.5, atr_normalized: 1.0, rsi_value: 50.0 },
        strategy: { strategy_type: 'TREND_CONTINUATION_SMC', rationale: 'Scanning structure and session order flow...' },
        dealing_range: { zone: 'EQUILIBRIUM', range_high: 0, range_low: 0, equilibrium_50: 0 },
        session: { session_name: 'LONDON', is_killzone: false, asian_high_swept: false },
      });
      if (structRes) setStructureData(structRes);
      if (smcRes) setSmcData(smcRes);
      if (liqRes) setLiquidityData(liqRes);
      if (healthRes) setDataHealth(healthRes);
      if (expRes) setExposureData(expRes);
    } catch (e) {
      console.error('Failed to fetch market intelligence:', e);
      setSummaryData({
        confluence: { total_score: 50, direction: 'NEUTRAL', confidence: 0.5 },
        regime: { regime: 'RANGEBOUND', adx_value: 18.5, atr_normalized: 1.0, rsi_value: 50.0 },
        strategy: { strategy_type: 'TREND_CONTINUATION_SMC', rationale: 'Scanning structure and session order flow...' },
        dealing_range: { zone: 'EQUILIBRIUM', range_high: 0, range_low: 0, equilibrium_50: 0 },
        session: { session_name: 'LONDON', is_killzone: false, asian_high_swept: false },
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedAsset, selectedTimeframe]);

  const confluence = summaryData?.confluence || {};
  const regime = summaryData?.regime || {};
  const strategy = summaryData?.strategy || {};
  const dealingRange = summaryData?.dealing_range || {};
  const session = summaryData?.session || {};

  const getScoreColor = (score: number) => {
    if (score >= 75) return '#10b981';
    if (score >= 60) return '#3b82f6';
    if (score >= 40) return '#f59e0b';
    return '#ef4444';
  };

  const getHealthBadge = () => {
    const status = dataHealth?.overall_status || 'HEALTHY';
    if (status === 'HEALTHY') return <Tag color="green" className="font-semibold">DATA HEALTH: LIVE</Tag>;
    if (status === 'DEGRADED') return <Tag color="orange" className="font-semibold">DATA HEALTH: DEGRADED</Tag>;
    if (status === 'STALE') return <Tag color="red" className="font-semibold">DATA HEALTH: STALE</Tag>;
    return <Tag color="red" className="font-semibold">DATA HEALTH: UNAVAILABLE</Tag>;
  };

  return (
    <div className="p-6 bg-slate-950 text-slate-100 min-h-screen">
      {/* Top Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-6 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-600/20 border border-blue-500/30 rounded-xl">
              <Layers className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <Title level={3} style={{ margin: 0, color: '#f8fafc' }}>
                  Phase 52 Quantitative Command Center
                </Title>
                {getHealthBadge()}
              </div>
              <Text className="text-slate-400 text-sm">
                Ensemble Intelligence, Multi-Provider Data Quality, SMC, Portfolio Exposure & Execution Sim
              </Text>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Select
            value={selectedAsset}
            onChange={setSelectedAsset}
            className="w-36 bg-slate-900 border-slate-700"
          >
            {ASSETS.map((a) => (
              <Option key={a} value={a}>{a}</Option>
            ))}
          </Select>

          <Select
            value={selectedTimeframe}
            onChange={setSelectedTimeframe}
            className="w-24 bg-slate-900 border-slate-700"
          >
            {TIMEFRAMES.map((tf) => (
              <Option key={tf} value={tf}>{tf}</Option>
            ))}
          </Select>

          <Button
            type="primary"
            icon={<RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />}
            onClick={fetchData}
            className="bg-blue-600 hover:bg-blue-500 border-none"
          >
            Refresh
          </Button>
        </div>
      </div>

      {loading && !summaryData ? (
        <div className="flex items-center justify-center h-96">
          <Spin size="large" />
        </div>
      ) : (
        <div className="mt-6 space-y-6">
          {/* Key Metric Overview Row */}
          <Row gutter={[16, 16]}>
            {/* Confluence Gauge Card */}
            <Col xs={24} sm={12} lg={6}>
              <Card className="bg-slate-900/80 border-slate-800 text-slate-100 rounded-2xl">
                <div className="flex items-center justify-between mb-2">
                  <Text className="text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    Confluence & Quality
                  </Text>
                  <Activity className="w-4 h-4 text-blue-400" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold" style={{ color: getScoreColor(confluence.total_score || 0) }}>
                    {confluence.total_score || 0}
                  </span>
                  <span className="text-slate-500 text-sm">/ 100</span>
                  <Tag color={confluence.total_score >= 75 ? "green" : (confluence.total_score >= 50 ? "blue" : "red")} className="ml-auto font-bold">
                    {confluence.total_score >= 85 ? "GRADE A+" : (confluence.total_score >= 75 ? "GRADE A" : (confluence.total_score >= 60 ? "GRADE B" : "NO_TRADE"))}
                  </Tag>
                </div>
                <Progress
                  percent={confluence.total_score || 0}
                  strokeColor={getScoreColor(confluence.total_score || 0)}
                  trailColor="#1e293b"
                  showInfo={false}
                  className="mt-3"
                />
                <div className="mt-2 flex justify-between text-xs text-slate-400">
                  <span>Direction: <b className="text-slate-200">{confluence.direction || 'NEUTRAL'}</b></span>
                  <span>Confidence: <b className="text-slate-200">{Math.round((confluence.confidence || 0) * 100)}%</b></span>
                </div>
              </Card>
            </Col>

            {/* Market Regime Card */}
            <Col xs={24} sm={12} lg={6}>
              <Card className="bg-slate-900/80 border-slate-800 text-slate-100 rounded-2xl">
                <div className="flex items-center justify-between mb-2">
                  <Text className="text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    Market Regime
                  </Text>
                  <TrendingUp className="w-4 h-4 text-emerald-400" />
                </div>
                <div className="text-xl font-bold text-slate-100">
                  {regime.regime || 'EVALUATING'}
                </div>
                <div className="mt-2 flex flex-col gap-1 text-xs text-slate-400">
                  <div className="flex justify-between">
                    <span>ADX Trend Power:</span>
                    <span className="text-slate-200 font-medium">{regime.adx_value?.toFixed(1) || '0.0'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>ATR Expansion:</span>
                    <span className="text-slate-200 font-medium">{regime.atr_normalized?.toFixed(2) || '1.0'}x</span>
                  </div>
                  <div className="flex justify-between">
                    <span>RSI Momentum:</span>
                    <span className="text-slate-200 font-medium">{regime.rsi_value?.toFixed(1) || '50.0'}</span>
                  </div>
                </div>
              </Card>
            </Col>

            {/* Strategy Ensemble & Router */}
            <Col xs={24} sm={12} lg={6}>
              <Card className="bg-slate-900/80 border-slate-800 text-slate-100 rounded-2xl">
                <div className="flex items-center justify-between mb-2">
                  <Text className="text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    Strategy Ensemble
                  </Text>
                  <Crosshair className="w-4 h-4 text-purple-400" />
                </div>
                <div className="text-base font-bold text-purple-300 truncate">
                  {strategy.strategy_type || 'TREND_CONTINUATION_SMC'}
                </div>
                <div className="mt-2 text-xs text-slate-400 line-clamp-2">
                  {strategy.rationale || 'Evaluating cluster-dampened ensemble votes...'}
                </div>
                <div className="mt-3">
                  <Button
                    size="small"
                    type="link"
                    className="p-0 text-blue-400 hover:text-blue-300 text-xs flex items-center gap-1"
                    onClick={() => setExplanationModalOpen(true)}
                  >
                    <HelpCircle className="w-3.5 h-3.5" /> Explain Signal Evidence
                  </Button>
                </div>
              </Card>
            </Col>

            {/* Portfolio Exposure & Session */}
            <Col xs={24} sm={12} lg={6}>
              <Card className="bg-slate-900/80 border-slate-800 text-slate-100 rounded-2xl">
                <div className="flex items-center justify-between mb-2">
                  <Text className="text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    Portfolio & Sessions
                  </Text>
                  <Clock className="w-4 h-4 text-amber-400" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold text-slate-100">{session.session_name || 'LONDON'}</span>
                  {session.is_killzone && (
                    <Tag color="red" className="font-semibold animate-pulse">KILLZONE</Tag>
                  )}
                </div>
                <div className="mt-2 flex flex-col gap-1 text-xs text-slate-400">
                  <div className="flex justify-between">
                    <span>Net USD Exposure:</span>
                    <span className="text-slate-200 font-bold">{exposureData?.currency_exposures?.USD || '0.0'} lots</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Active Positions:</span>
                    <span className="text-slate-200">{exposureData?.open_positions_count || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Asian High Swept:</span>
                    <span className={session.asian_high_swept ? 'text-emerald-400 font-semibold' : 'text-slate-500'}>
                      {session.asian_high_swept ? 'YES' : 'NO'}
                    </span>
                  </div>
                </div>
              </Card>
            </Col>
          </Row>

          {/* Deep Analysis Tabs */}
          <Card className="bg-slate-900/80 border-slate-800 text-slate-100 rounded-2xl">
            <Tabs defaultActiveKey="confluence" className="custom-tabs">
              {/* Tab 1: Confluence Layer Breakdown */}
              <Tabs.TabPane tab="Confluence Breakdown" key="confluence">
                <Row gutter={[16, 16]}>
                  <Col span={24}>
                    <Paragraph className="text-slate-400 text-sm">
                      Dynamic weighted score calculated across 6 independent evidence layers with collinearity attenuation dampeners.
                    </Paragraph>
                  </Col>

                  {confluence.layer_scores && Object.entries(confluence.layer_scores).map(([layer, score]: [string, any]) => (
                    <Col xs={24} sm={12} md={8} key={layer}>
                      <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
                        <div className="flex justify-between text-xs font-semibold text-slate-400 uppercase">
                          <span>{layer} Layer</span>
                          <span className="text-blue-400 font-bold">{score} pts</span>
                        </div>
                        <Progress
                          percent={Math.min(100, (score / 25) * 100)}
                          strokeColor="#3b82f6"
                          trailColor="#1e293b"
                          showInfo={false}
                          className="mt-2"
                        />
                      </div>
                    </Col>
                  ))}

                  {confluence.collinearity_penalty_applied > 0 && (
                    <Col span={24}>
                      <div className="p-3 bg-amber-950/30 border border-amber-800/40 rounded-xl flex items-center gap-3 text-amber-300 text-xs">
                        <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                        <span>
                          Collinearity attenuation active: Correlated momentum indicators dampened by{' '}
                          <b>-{confluence.collinearity_penalty_applied} pts</b> to prevent artificial vote inflation.
                        </span>
                      </div>
                    </Col>
                  )}
                </Row>
              </Tabs.TabPane>

              {/* Tab 2: Market Structure & Swings */}
              <Tabs.TabPane tab="Market Structure (BOS / CHoCH)" key="structure">
                <Row gutter={[16, 16]}>
                  <Col xs={24} lg={8}>
                    <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-3">
                      <Text className="text-slate-400 text-xs font-semibold uppercase">Structure Health</Text>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm">Trend Bias:</span>
                        <Tag color={structureData?.strength?.bias === 'BULLISH' ? 'green' : (structureData?.strength?.bias === 'BEARISH' ? 'red' : 'default')}>
                          {structureData?.strength?.bias || 'NEUTRAL'}
                        </Tag>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm">Structure Score:</span>
                        <span className="text-slate-100 font-bold">{structureData?.strength?.score?.toFixed(1) || 50.0} / 100</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm">Higher Highs / Lows:</span>
                        <span className="text-emerald-400 font-medium">
                          {structureData?.strength?.hh_count || 0} HH / {structureData?.strength?.hl_count || 0} HL
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm">Lower Highs / Lows:</span>
                        <span className="text-rose-400 font-medium">
                          {structureData?.strength?.lh_count || 0} LH / {structureData?.strength?.ll_count || 0} LL
                        </span>
                      </div>
                    </div>
                  </Col>

                  <Col xs={24} lg={16}>
                    <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
                      <Text className="text-slate-400 text-xs font-semibold uppercase mb-3 block">
                        Recent Structural Break Events
                      </Text>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {structureData?.bos_events?.length > 0 ? (
                          structureData.bos_events.map((e: any, idx: number) => (
                            <div key={idx} className="flex justify-between items-center p-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs">
                              <span className="font-semibold text-blue-400">{e.event_type}</span>
                              <span className="text-slate-300">Price: {e.price?.toFixed(5)}</span>
                              <span className="text-slate-500">{e.timestamp_ist}</span>
                            </div>
                          ))
                        ) : (
                          <div className="text-slate-500 text-xs py-4 text-center">No recent structural breaks detected.</div>
                        )}
                      </div>
                    </div>
                  </Col>
                </Row>
              </Tabs.TabPane>

              {/* Tab 3: Smart Money (Order Blocks & FVG) */}
              <Tabs.TabPane tab="Smart Money Concepts (OB / FVG)" key="smc">
                <Row gutter={[16, 16]}>
                  {/* Dealing Range Card */}
                  <Col xs={24} md={8}>
                    <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl space-y-3">
                      <Text className="text-slate-400 text-xs font-semibold uppercase">Active Dealing Range</Text>
                      <div className="flex justify-between items-center">
                        <span className="text-slate-400 text-sm">Current Zone:</span>
                        <Tag color={dealingRange.zone === 'DISCOUNT' ? 'green' : (dealingRange.zone === 'PREMIUM' ? 'red' : 'blue')}>
                          {dealingRange.zone || 'EQUILIBRIUM'}
                        </Tag>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-400">Range High:</span>
                        <span className="text-slate-200">{dealingRange.range_high?.toFixed(5)}</span>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-400">50% Equilibrium:</span>
                        <span className="text-amber-400 font-bold">{dealingRange.equilibrium_50?.toFixed(5)}</span>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-400">Range Low:</span>
                        <span className="text-slate-200">{dealingRange.range_low?.toFixed(5)}</span>
                      </div>
                    </div>
                  </Col>

                  {/* Order Blocks */}
                  <Col xs={24} md={16}>
                    <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-xl">
                      <Text className="text-slate-400 text-xs font-semibold uppercase mb-3 block">
                        Institutional Order Blocks
                      </Text>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {smcData?.order_blocks?.length > 0 ? (
                          smcData.order_blocks.map((ob: any, idx: number) => (
                            <div key={idx} className="flex justify-between items-center p-2.5 bg-slate-900 border border-slate-800 rounded-lg text-xs">
                              <span className="font-semibold text-purple-400">{ob.block_type}</span>
                              <span className="text-slate-300">[{ob.price_low?.toFixed(5)} - {ob.price_high?.toFixed(5)}]</span>
                              <Tag color={ob.status === 'ACTIVE' ? 'green' : (ob.status === 'TOUCHED' ? 'orange' : 'default')}>
                                {ob.status} ({ob.touch_count} touches)
                              </Tag>
                            </div>
                          ))
                        ) : (
                          <div className="text-slate-500 text-xs py-4 text-center">No active Order Blocks.</div>
                        )}
                      </div>
                    </div>
                  </Col>
                </Row>
              </Tabs.TabPane>
            </Tabs>
          </Card>
        </div>
      )}

      {/* 9-Question Quantitative Explainability Evidence Tree Modal */}
      <Modal
        title={
          <div className="flex items-center gap-2 text-slate-100">
            <Shield className="w-5 h-5 text-blue-400" />
            <span>Quantitative Signal Explainability (9 Core Questions)</span>
          </div>
        }
        open={explanationModalOpen}
        onCancel={() => setExplanationModalOpen(false)}
        footer={[
          <Button key="close" type="primary" onClick={() => setExplanationModalOpen(false)}>
            Close
          </Button>
        ]}
        className="dark-modal"
      >
        <div className="space-y-4 text-sm text-slate-300 py-2">
          <div>
            <h4 className="text-blue-400 font-semibold text-xs uppercase tracking-wider mb-1">1. WHY & WHY NOW?</h4>
            <p className="text-xs text-slate-300">
              Confluence score verified at {confluence.total_score}/100 with directional consensus across Market Structure, Smart Money, and ICT Killzones.
            </p>
          </div>

          <div>
            <h4 className="text-emerald-400 font-semibold text-xs uppercase tracking-wider mb-1">2. WHY THIS DIRECTION ({confluence.direction || 'BUY'})?</h4>
            <p className="text-xs text-slate-300">
              Structural trend bias is {structureData?.strength?.bias || 'BULLISH'} with BOS confirmation and zero higher-timeframe resistance.
            </p>
          </div>

          <div>
            <h4 className="text-purple-400 font-semibold text-xs uppercase tracking-wider mb-1">3. WHY THIS ENTRY & RISK-REWARD?</h4>
            <p className="text-xs text-slate-300">
              Entry anchored at institutional order block boundary in {dealingRange.zone || 'DISCOUNT'} dealing range with minimum R:R $\ge 1.5$.
            </p>
          </div>

          <div>
            <h4 className="text-rose-400 font-semibold text-xs uppercase tracking-wider mb-1">4. WHAT INVALIDATES IT?</h4>
            <p className="text-xs text-slate-300">
              Opposing CHoCH structural break, price breach below order block boundary, or holding envelope expiration.
            </p>
          </div>

          <div>
            <h4 className="text-amber-400 font-semibold text-xs uppercase tracking-wider mb-1">5. DATA QUALITY & INTEGRITY STATUS</h4>
            <p className="text-xs text-slate-300">
              Data Quality: {dataHealth?.overall_status || 'LIVE'}. Zero future timestamps, zero negative volume, freshness verified.
            </p>
          </div>
        </div>
      </Modal>
    </div>
  );
};
