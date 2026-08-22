import React, { useEffect, useState } from 'react';
import { Card, Table, Typography, Spin, Space, Tag, Row, Col, Statistic } from 'antd';
import { ExperimentOutlined, CheckCircleOutlined, InfoCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

export const ModelComparisonLab: React.FC = () => {
  const [benchmarks, setBenchmarks] = useState<any>(null);
  const [abTest, setAbTest] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchValidationData = async () => {
      try {
        const [benchRes, abRes] = await Promise.all([
          fetch('/api/v1/validation/benchmark'),
          fetch('/api/v1/validation/ab-test?config_a=A&config_b=B')
        ]);
        setBenchmarks(await benchRes.json());
        setAbTest(await abRes.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchValidationData();
  }, []);

  if (loading) return <Spin size="large" className="flex justify-center mt-20" />;

  const benchmarkColumns = [
    { title: 'Model', dataIndex: 'model', key: 'model' },
    { title: 'Accuracy', dataIndex: 'accuracy', key: 'accuracy', render: (val: number) => `${(val * 100).toFixed(1)}%` },
    { title: 'MAE', dataIndex: 'mae', key: 'mae' },
    { title: 'RMSE', dataIndex: 'rmse', key: 'rmse' },
    { title: 'Sharpe', dataIndex: 'sharpe', key: 'sharpe' },
    { title: 'Max Drawdown', dataIndex: 'drawdown', key: 'drawdown', render: (val: number) => <Text type="danger">{val}%</Text> },
  ];

  const benchmarkData = benchmarks ? Object.keys(benchmarks).map((key) => ({
    key,
    model: key.toUpperCase(),
    accuracy: benchmarks[key].directional_accuracy,
    mae: benchmarks[key].mae,
    rmse: benchmarks[key].rmse,
    sharpe: benchmarks[key].sharpe_ratio,
    drawdown: benchmarks[key].max_drawdown_pct,
  })) : [];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center space-x-3 border-b border-gray-700 pb-4">
        <ExperimentOutlined className="text-3xl text-purple-400" />
        <Title level={2} className="!mb-0 text-gray-100">Benchmarking & A/B Testing Lab</Title>
      </div>

      <Card title="Model Benchmark Comparison" className="bg-gray-800 border-gray-700">
        <Table columns={benchmarkColumns} dataSource={benchmarkData} pagination={false} className="dark-theme-table" />
      </Card>

      {abTest && (
        <Card title="Live A/B Testing Results" className="bg-gray-800 border-gray-700">
          <Row gutter={16}>
            <Col span={12}>
              <Card type="inner" title={`Config A (${abTest.config_a})`} className="bg-gray-900 border-gray-700">
                <Statistic title="Profitability" value={abTest.metrics.config_a.profitability} precision={2} suffix="%" valueStyle={{ color: '#3f8600' }} />
                <Statistic title="Decision Quality" value={abTest.metrics.config_a.decision_quality} />
                <Statistic title="Risk Score" value={abTest.metrics.config_a.risk_score} valueStyle={{ color: '#cf1322' }} />
              </Card>
            </Col>
            <Col span={12}>
              <Card type="inner" title={`Config B (${abTest.config_b})`} className="bg-gray-900 border-gray-700">
                <Statistic title="Profitability" value={abTest.metrics.config_b.profitability} precision={2} suffix="%" valueStyle={{ color: '#3f8600' }} />
                <Statistic title="Decision Quality" value={abTest.metrics.config_b.decision_quality} />
                <Statistic title="Risk Score" value={abTest.metrics.config_b.risk_score} valueStyle={{ color: '#cf1322' }} />
              </Card>
            </Col>
          </Row>
          <div className="mt-4 p-4 bg-gray-900 rounded-md border border-gray-700 flex items-center space-x-2">
            <CheckCircleOutlined className="text-green-500 text-xl" />
            <Text className="text-gray-200"><strong className="text-white">Winner: {abTest.winner.toUpperCase()}</strong> - {abTest.conclusion}</Text>
          </div>
        </Card>
      )}
    </div>
  );
};
