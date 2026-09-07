import React, { useEffect, useState } from 'react';
import { Card, Typography, Row, Col, Statistic, Progress, Spin, Tag } from 'antd';
import { DashboardOutlined, CheckCircleOutlined, SyncOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

export const SystemHealth: React.FC = () => {
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch('/api/v1/enterprise/health');
        if (res.ok) {
          const data = await res.json();
          setHealth(data);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchHealth();
    // Poll every 5s
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const safeHealth = health || {
    cpu_usage_pct: 0,
    memory_usage_pct: 0,
    storage_usage_pct: 0,
    status: 'healthy',
    api_latency_ms: 5,
    backend: 'online',
    frontend: 'online',
    forecast_engine: 'online',
    decision_engine: 'online',
    market_database: 'connected',
    websocket: 'active',
  };

  const getStatusTag = (status: string) => {
    const s = (status || '').toLowerCase();
    return s === 'online' || s === 'healthy' || s === 'connected' || s === 'active' || s === 'ok' 
      ? <Tag color="green">{(status || 'ONLINE').toUpperCase()}</Tag>
      : <Tag color="red">{(status || 'OFFLINE').toUpperCase()}</Tag>;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-gray-700 pb-4">
        <div className="flex items-center space-x-3">
          <DashboardOutlined className="text-3xl text-emerald-400" />
          <Title level={2} className="!mb-0 text-gray-100">System Health Center</Title>
        </div>
        <SyncOutlined spin className="text-gray-500" />
      </div>

      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Card title="Hardware Metrics" className="bg-gray-800 border-gray-700 h-full">
            <div className="mb-4">
              <Text className="text-gray-400">CPU Usage</Text>
              <Progress percent={safeHealth.cpu_usage_pct} status={safeHealth.cpu_usage_pct > 80 ? 'exception' : 'active'} />
            </div>
            <div className="mb-4">
              <Text className="text-gray-400">Memory Usage</Text>
              <Progress percent={safeHealth.memory_usage_pct} status={safeHealth.memory_usage_pct > 80 ? 'exception' : 'normal'} />
            </div>
            <div>
              <Text className="text-gray-400">Storage Usage</Text>
              <Progress percent={safeHealth.storage_usage_pct} status="normal" />
            </div>
          </Card>
        </Col>

        <Col span={16}>
          <Card title="Service Status" className="bg-gray-800 border-gray-700 h-full">
            <Row gutter={[16, 16]}>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">Overall Status</Text> {getStatusTag(safeHealth.status)}
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">API Latency</Text> <Text className="text-white">{safeHealth.api_latency_ms} ms</Text>
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">Backend</Text> {getStatusTag(safeHealth.backend)}
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">Frontend</Text> {getStatusTag(safeHealth.frontend)}
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">Forecast Engine</Text> {getStatusTag(safeHealth.forecast_engine)}
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">Decision Engine</Text> {getStatusTag(safeHealth.decision_engine)}
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">Market Database</Text> {getStatusTag(safeHealth.market_database)}
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">WebSocket</Text> {getStatusTag(safeHealth.websocket)}
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};
