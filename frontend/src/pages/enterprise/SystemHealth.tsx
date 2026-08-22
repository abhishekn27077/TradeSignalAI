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
        setHealth(await res.json());
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

  if (loading && !health) return <Spin size="large" className="flex justify-center mt-20" />;

  const getStatusTag = (status: string) => {
    return status === 'online' || status === 'healthy' || status === 'connected' || status === 'active' 
      ? <Tag color="green">{status.toUpperCase()}</Tag>
      : <Tag color="red">{status.toUpperCase()}</Tag>;
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
              <Progress percent={health.cpu_usage_pct} status={health.cpu_usage_pct > 80 ? 'exception' : 'active'} />
            </div>
            <div className="mb-4">
              <Text className="text-gray-400">Memory Usage</Text>
              <Progress percent={health.memory_usage_pct} status={health.memory_usage_pct > 80 ? 'exception' : 'normal'} />
            </div>
            <div>
              <Text className="text-gray-400">Storage Usage</Text>
              <Progress percent={health.storage_usage_pct} status="normal" />
            </div>
          </Card>
        </Col>

        <Col span={16}>
          <Card title="Service Status" className="bg-gray-800 border-gray-700 h-full">
            <Row gutter={[16, 16]}>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">Overall Status</Text> {getStatusTag(health.status)}
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">API Latency</Text> <Text className="text-white">{health.api_latency_ms} ms</Text>
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">Backend</Text> {getStatusTag(health.backend)}
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">Frontend</Text> {getStatusTag(health.frontend)}
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">Forecast Engine</Text> {getStatusTag(health.forecast_engine)}
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">Decision Engine</Text> {getStatusTag(health.decision_engine)}
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">Market Database</Text> {getStatusTag(health.market_database)}
              </Col>
              <Col span={12} className="flex justify-between border-b border-gray-700 pb-2">
                <Text className="text-gray-300">WebSocket</Text> {getStatusTag(health.websocket)}
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};
