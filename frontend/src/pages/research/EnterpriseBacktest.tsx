import React, { useEffect, useState } from 'react';
import { Card, Button, Input, Select, Spin, Typography, Row, Col, Alert } from 'antd';
import { SyncOutlined, CheckCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

export const EnterpriseBacktest: React.FC = () => {
  const [walkForward, setWalkForward] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchWalkForward = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/validation/walk-forward');
      setWalkForward(await res.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWalkForward();
  }, []);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center space-x-3 border-b border-gray-700 pb-4">
        <SyncOutlined className="text-3xl text-cyan-400" />
        <Title level={2} className="!mb-0 text-gray-100">Walk-Forward Validation & Backtesting</Title>
      </div>
      
      <Card title="Run Configuration" className="bg-gray-800 border-gray-700">
        <div className="grid grid-cols-2 gap-4">
          <Input placeholder="Strategy/Model" defaultValue="Kronos" className="dark-theme-input" />
          <Input placeholder="Symbol" defaultValue="BTCUSD" className="dark-theme-input" />
          <Select defaultValue="1h" options={[{value: '1h', label: '1 Hour'}, {value: '4h', label: '4 Hour'}]} />
          <Input placeholder="Initial Capital" defaultValue="10000" type="number" className="dark-theme-input" />
        </div>
        <Button type="primary" className="mt-4" onClick={fetchWalkForward}>Run Walk-Forward Backtest</Button>
      </Card>
      
      {loading ? (
        <Spin size="large" className="flex justify-center mt-10" />
      ) : walkForward ? (
        <Card title="Walk-Forward Results" className="bg-gray-800 border-gray-700">
          <Row gutter={[16, 16]}>
            <Col span={8}>
              <Card type="inner" title="Data Splits" className="bg-gray-900 border-gray-700">
                <p><Text className="text-gray-400">Training:</Text> <Text strong className="text-white">{walkForward.training_window_size}</Text></p>
                <p><Text className="text-gray-400">Validation:</Text> <Text strong className="text-white">{walkForward.validation_window_size}</Text></p>
                <p><Text className="text-gray-400">Forward Test:</Text> <Text strong className="text-white">{walkForward.forward_test_window_size}</Text></p>
              </Card>
            </Col>
            <Col span={16}>
              <Card type="inner" title="Analysis" className="bg-gray-900 border-gray-700">
                <p><Text className="text-gray-400">Windows Processed:</Text> <Text strong className="text-white">{walkForward.windows_processed}</Text></p>
                <p><Text className="text-gray-400">Out-Of-Sample Accuracy:</Text> <Text strong className="text-white">{(walkForward.average_out_of_sample_accuracy * 100).toFixed(1)}%</Text></p>
                {walkForward.overfitting_detected ? (
                  <Alert message="Overfitting Detected in recent windows" type="error" showIcon className="mt-2" />
                ) : (
                  <Alert message="Model Generalization Stable" type="success" showIcon className="mt-2" />
                )}
              </Card>
            </Col>
          </Row>
          <div className="mt-4 p-4 bg-gray-900 rounded-md border border-gray-700 flex items-center space-x-2">
            <CheckCircleOutlined className="text-blue-500 text-xl" />
            <Text className="text-gray-200"><strong className="text-white">Conclusion:</strong> {walkForward.recommendation}</Text>
          </div>
        </Card>
      ) : null}
    </div>
  );
};
