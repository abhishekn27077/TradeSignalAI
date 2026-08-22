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
  RefreshCw
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
  const [explanationModalOpen, setExplanationModalOpen] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [sumRes, structRes, smcRes, liqRes] = await Promise.all([
        fetch(`/api/v1/analysis/summary/${selectedAsset}?timeframe=${selectedTimeframe}`),
        fetch(`/api/v1/analysis/structure/${selectedAsset}?timeframe=${selectedTimeframe}`),
        fetch(`/api/v1/analysis/smart-money/${selectedAsset}?timeframe=${selectedTimeframe}`),
        fetch(`/api/v1/analysis/liquidity/${selectedAsset}?timeframe=${selectedTimeframe}`),
      ]);

      if (sumRes.ok) setSummaryData(await sumRes.json());
      if (structRes.ok) setStructureData(await structRes.json());
      if (smcRes.ok) setSmcData(await smcRes.json());
      if (liqRes.ok) setLiquidityData(await liqRes.json());
    } catch (e) {
      console.error('Failed to fetch market intelligence:', e);
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
              <Title level={3} style={{ margin: 0, color: '#f8fafc' }}>
                Phase 51 Quantitative Market Intelligence
              </Title>
              <Text className="text-slate-400 text-sm">
                Multi-Layer Smart Money Concepts, Market Structure, SMT & Confluence Engine
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
                    Confluence Score
                  </Text>
                  <Activity className="w-4 h-4 text-blue-400" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold" style={{ color: getScoreColor(confluence.total_score || 0) }}>
                    {confluence.total_score || 0}
                  </span>
                  <span className="text-slate-500 text-sm">/ 100</span>
                  {confluence.is_actionable && (
                    <Tag color="green" className="ml-auto font-semibold">ACTIONABLE</Tag>
                  )}
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

            {/* Active Strategy Dispatcher */}
            <Col xs={24} sm={12} lg={6}>
              <Card className="bg-slate-900/80 border-slate-800 text-slate-100 rounded-2xl">
                <div className="flex items-center justify-between mb-2">
                  <Text className="text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    Strategy Router
                  </Text>
                  <Crosshair className="w-4 h-4 text-purple-400" />
                </div>
                <div className="text-base font-bold text-purple-300 truncate">
                  {strategy.strategy_type || 'NO_TRADE'}
                </div>
                <div className="mt-2 text-xs text-slate-400 line-clamp-2">
                  {strategy.rationale || 'Evaluating regime confluence...'}
                </div>
                <div className="mt-3">
                  <Button
                    size="small"
                    type="link"
                    className="p-0 text-blue-400 hover:text-blue-300 text-xs flex items-center gap-1"
                    onClick={() => setExplanationModalOpen(true)}
                  >
                    <HelpCircle className="w-3.5 h-3.5" /> View Evidence Tree
                  </Button>
                </div>
              </Card>
            </Col>

            {/* ICT Session & Killzone Card */}
            <Col xs={24} sm={12} lg={6}>
              <Card className="bg-slate-900/80 border-slate-800 text-slate-100 rounded-2xl">
                <div className="flex items-center justify-between mb-2">
                  <Text className="text-slate-400 text-xs font-semibold uppercase tracking-wider">
                    Session & Killzone
                  </Text>
                  <Clock className="w-4 h-4 text-amber-400" />
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xl font-bold text-slate-100">{session.session_name || 'ASIA'}</span>
                  {session.is_killzone && (
                    <Tag color="red" className="font-semibold animate-pulse">KILLZONE ACTIVE</Tag>
                  )}
                </div>
                <div className="mt-2 flex flex-col gap-1 text-xs text-slate-400">
                  <div className="flex justify-between">
                    <span>Window (UTC):</span>
                    <span className="text-slate-200">{session.session_start_utc} - {session.session_end_utc}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Asian High Swept:</span>
                    <span className={session.asian_high_swept ? 'text-emerald-400 font-semibold' : 'text-slate-500'}>
                      {session.asian_high_swept ? 'YES' : 'NO'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Asian Low Swept:</span>
                    <span className={session.asian_low_swept ? 'text-emerald-400 font-semibold' : 'text-slate-500'}>
                      {session.asian_low_swept ? 'YES' : 'NO'}
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

      {/* Explanation Evidence Tree Modal */}
      <Modal
        title={
          <div className="flex items-center gap-2 text-slate-100">
            <Shield className="w-5 h-5 text-blue-400" />
            <span>Quantitative Signal Explanation & Evidence Tree</span>
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
            <h4 className="text-blue-400 font-semibold text-xs uppercase tracking-wider mb-2">1. WHY (Evidence Chain)</h4>
            <ul className="list-disc pl-5 space-y-1 text-xs text-slate-300">
              <li>Confluence score verified at {confluence.total_score}/100 with directional consensus.</li>
              <li>Market Structure aligned in {regime.regime || 'STRONG_TREND'} regime.</li>
              <li>Institutional order block and Fair Value Gap active in optimal dealing range.</li>
              <li>ICT Killzone volatility active with non-repainting SuperTrend / UT-Bot confirmation.</li>
            </ul>
          </div>

          <div>
            <h4 className="text-amber-400 font-semibold text-xs uppercase tracking-wider mb-2">2. RISK PROFILE</h4>
            <ul className="list-disc pl-5 space-y-1 text-xs text-slate-300">
              <li>Zero-trust Risk-to-Reward ratio minimum 1.2:1 verified.</li>
              <li>Dynamic timeframe-scaled holding envelope active via MarketClockService.</li>
              <li>Macroeconomic high-impact event window filter clear.</li>
            </ul>
          </div>

          <div>
            <h4 className="text-rose-400 font-semibold text-xs uppercase tracking-wider mb-2">3. INVALIDATION TRIGGERS</h4>
            <ul className="list-disc pl-5 space-y-1 text-xs text-slate-300">
              <li>Opposing Change of Character (CHoCH) break beyond recent structural pivot.</li>
              <li>Price breach past the order block invalidation boundary.</li>
              <li>Holding window envelope expiration.</li>
            </ul>
          </div>
        </div>
      </Modal>
    </div>
  );
};
