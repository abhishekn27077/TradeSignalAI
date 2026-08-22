import React, { useState, useEffect } from 'react';
import { Card, Typography, Row, Col, Tag, Statistic } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';

const { Title } = Typography;

export const MarketHeatmap: React.FC = () => {
  const [heatmapData, setHeatmapData] = useState<any>(null);

  useEffect(() => {
    // Stub
    setHeatmapData({
      bullish_assets: ['BTCUSD', 'ETHUSD', 'SOLUSD'],
      bearish_assets: ['XRPUSD', 'ADAUSD'],
      neutral_assets: ['DOTUSD'],
      strong_trend: ['BTCUSD', 'SOLUSD'],
      highest_confidence: { symbol: 'BTCUSD', confidence: 0.94 },
      lowest_confidence: { symbol: 'DOTUSD', confidence: 0.52 }
    });
  }, []);

  if (!heatmapData) return <div>Loading...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Market Heatmap</Title>
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Card title="Bullish Assets" style={{ borderColor: '#52c41a' }}>
            {heatmapData.bullish_assets.map((a: string) => <Tag color="green" key={a}>{a}</Tag>)}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Bearish Assets" style={{ borderColor: '#f5222d' }}>
            {heatmapData.bearish_assets.map((a: string) => <Tag color="red" key={a}>{a}</Tag>)}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Neutral Assets">
            {heatmapData.neutral_assets.map((a: string) => <Tag color="default" key={a}>{a}</Tag>)}
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic 
              title="Highest Confidence" 
              value={heatmapData.highest_confidence?.symbol} 
              suffix={`${(heatmapData.highest_confidence?.confidence * 100).toFixed(1)}%`} 
              valueStyle={{ color: '#3f8600' }} 
              prefix={<ArrowUpOutlined />} 
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <Statistic 
              title="Lowest Confidence" 
              value={heatmapData.lowest_confidence?.symbol} 
              suffix={`${(heatmapData.lowest_confidence?.confidence * 100).toFixed(1)}%`} 
              valueStyle={{ color: '#cf1322' }} 
              prefix={<ArrowDownOutlined />} 
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
