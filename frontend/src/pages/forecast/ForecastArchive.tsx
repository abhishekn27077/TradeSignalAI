import React from 'react';
import { Card, Typography, Table, Tag } from 'antd';

const { Title } = Typography;

export const ForecastArchive: React.FC = () => {
  // Stub data
  const columns = [
    { title: 'Symbol', dataIndex: 'symbol', key: 'symbol' },
    { title: 'Direction', dataIndex: 'direction', key: 'direction', render: (d: string) => <Tag color={d === 'BULLISH' ? 'green' : 'red'}>{d}</Tag> },
    { title: 'Grade', dataIndex: 'grade', key: 'grade' },
    { title: 'Archived At', dataIndex: 'archived_at', key: 'archived' }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Forecast Archive</Title>
      <Card title="Historical Predictions">
        <Table columns={columns} dataSource={[]} rowKey="id" />
      </Card>
    </div>
  );
};
