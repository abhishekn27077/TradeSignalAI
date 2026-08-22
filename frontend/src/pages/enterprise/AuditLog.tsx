import React, { useEffect, useState } from 'react';
import { Card, Typography, Table, Spin, Tag, Input } from 'antd';
import { SafetyCertificateOutlined, SearchOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

const { Title } = Typography;

export const AuditLog: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch('/api/v1/enterprise/audit', {
            headers: { 'X-API-Key': 'ENTERPRISE_DEV_KEY' }
        });
        setLogs(await res.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  const columns = [
    { 
      title: 'Timestamp', 
      dataIndex: 'timestamp', 
      key: 'timestamp',
      render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm:ss')
    },
    { 
      title: 'Action', 
      dataIndex: 'action', 
      key: 'action',
      render: (a: string) => <Tag color="blue">{a}</Tag>
    },
    { title: 'User / System', dataIndex: 'user', key: 'user' },
    { title: 'Details', dataIndex: 'details', key: 'details' },
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center space-x-3 border-b border-gray-700 pb-4">
        <SafetyCertificateOutlined className="text-3xl text-yellow-500" />
        <Title level={2} className="!mb-0 text-gray-100">Security & Audit Trail</Title>
      </div>

      <Card className="bg-gray-800 border-gray-700">
        <div className="mb-4">
            <Input prefix={<SearchOutlined />} placeholder="Search audit logs..." className="max-w-md dark-theme-input" />
        </div>
        {loading ? (
          <Spin size="large" className="flex justify-center" />
        ) : (
          <Table 
            columns={columns} 
            dataSource={logs.map((l, i) => ({ ...l, key: i }))} 
            pagination={{ pageSize: 10 }}
            className="dark-theme-table"
          />
        )}
      </Card>
    </div>
  );
};
