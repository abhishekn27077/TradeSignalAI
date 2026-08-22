import React, { useEffect, useState } from 'react';
import { Card, Typography, Spin, Form, Switch, InputNumber, Button, message } from 'antd';
import { SettingOutlined, SaveOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

export const ConfigurationCenter: React.FC = () => {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await fetch('/api/v1/enterprise/config');
        setConfig(await res.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchConfig();
  }, []);

  const handleSave = () => {
    message.success('Configuration updated successfully (Stub)');
  };

  if (loading) return <Spin size="large" className="flex justify-center mt-20" />;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-gray-700 pb-4">
        <div className="flex items-center space-x-3">
          <SettingOutlined className="text-3xl text-gray-300" />
          <Title level={2} className="!mb-0 text-gray-100">Configuration Center</Title>
        </div>
        <Button type="primary" icon={<SaveOutlined />} onClick={handleSave}>Save Changes</Button>
      </div>

      <Form layout="vertical">
        <div className="grid grid-cols-2 gap-6">
          <Card title="Forecast Settings" className="bg-gray-800 border-gray-700">
            <Form.Item label={<Text className="text-gray-300">Enable Forecasting</Text>}>
              <Switch defaultChecked={config?.forecast_settings.enabled} />
            </Form.Item>
            <Form.Item label={<Text className="text-gray-300">Max Concurrent Models</Text>}>
              <InputNumber min={1} max={10} defaultValue={config?.forecast_settings.max_concurrent_models} />
            </Form.Item>
          </Card>

          <Card title="Database Settings" className="bg-gray-800 border-gray-700">
            <Form.Item label={<Text className="text-gray-300">Connection Pool Size</Text>}>
              <InputNumber min={5} max={100} defaultValue={config?.database_settings.pool_size} />
            </Form.Item>
            <Form.Item label={<Text className="text-gray-300">Query Timeout (s)</Text>}>
              <InputNumber min={10} max={120} defaultValue={config?.database_settings.timeout} />
            </Form.Item>
          </Card>

          <Card title="Risk Settings" className="bg-gray-800 border-gray-700">
            <Form.Item label={<Text className="text-gray-300">Max Drawdown Limit (%)</Text>}>
              <InputNumber min={1} max={20} defaultValue={config?.risk_settings.max_drawdown_limit} />
            </Form.Item>
            <Form.Item label={<Text className="text-gray-300">Max Position Size (%)</Text>}>
              <InputNumber min={0.5} max={10} defaultValue={config?.risk_settings.max_position_size} />
            </Form.Item>
          </Card>
        </div>
      </Form>
    </div>
  );
};
