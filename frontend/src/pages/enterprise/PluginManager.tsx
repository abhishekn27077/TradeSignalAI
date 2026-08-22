import React, { useEffect, useState } from 'react';
import { Card, Typography, List, Tag, Spin, Button, message } from 'antd';
import { AppstoreAddOutlined, CloudUploadOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

export const PluginManager: React.FC = () => {
  const [plugins, setPlugins] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlugins = async () => {
      try {
        const res = await fetch('/api/v1/enterprise/plugins');
        setPlugins(await res.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchPlugins();
  }, []);

  const handleUpload = () => {
    message.info('Plugin upload triggered (Stub)');
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between border-b border-gray-700 pb-4">
        <div className="flex items-center space-x-3">
          <AppstoreAddOutlined className="text-3xl text-pink-400" />
          <Title level={2} className="!mb-0 text-gray-100">Plugin Architecture</Title>
        </div>
        <Button icon={<CloudUploadOutlined />} onClick={handleUpload}>Install Plugin</Button>
      </div>

      <Card className="bg-gray-800 border-gray-700">
        <div className="mb-4">
          <Text className="text-gray-300">System is configured to hot-load external modules from the <code className="bg-gray-700 p-1 rounded">plugins/</code> directory.</Text>
        </div>
        
        {loading ? (
          <Spin size="large" className="flex justify-center" />
        ) : (
          <List
            header={<div>Loaded Extensions ({plugins?.count})</div>}
            bordered
            dataSource={plugins?.active_plugins || []}
            renderItem={(item: string) => (
              <List.Item className="flex justify-between">
                <Text className="text-white font-mono">{item}</Text>
                <Tag color="success">ACTIVE</Tag>
              </List.Item>
            )}
            className="bg-gray-900 border-gray-700 text-gray-200"
          />
        )}
      </Card>
    </div>
  );
};
