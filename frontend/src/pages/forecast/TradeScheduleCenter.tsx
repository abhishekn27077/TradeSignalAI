import React, { useState, useEffect } from 'react';
import { Card, Typography, Table, Badge, Space, Alert, Progress } from 'antd';
import { ClockCircleOutlined, CalendarOutlined, CheckCircleOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

export const TradeScheduleCenter: React.FC = () => {
  const [scheduleData, setScheduleData] = useState<any>(null);

  useEffect(() => {
    // Stub fetch
    setScheduleData({
      current_time_ist: new Date().toISOString(),
      next_h4_time_ist: new Date(Date.now() + 3600000).toISOString(),
      countdown_seconds: 3600,
      planner: [
        { forecast_time_ist: new Date(Date.now() + 3600000).toISOString(), status: 'Generating' },
        { forecast_time_ist: new Date(Date.now() + 18000000).toISOString(), status: 'Scheduled' },
      ]
    });
  }, []);

  if (!scheduleData) return <Progress type="circle" />;

  const columns = [
    { title: 'Forecast Time (IST)', dataIndex: 'forecast_time_ist', key: 'time', render: (val: string) => new Date(val).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' }) },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (status: string) => <Badge status={status === 'Generating' ? 'processing' : 'default'} text={status} /> },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Trade Schedule Center</Title>
      <Alert 
        message="Next Forecast Generation" 
        description={`Next H4 Candle in ${Math.floor(scheduleData.countdown_seconds / 60)} minutes`}
        type="info" 
        showIcon 
        icon={<ClockCircleOutlined />}
        style={{ marginBottom: 24 }}
      />
      <Card title="H4 Session Planner (IST)">
        <Table dataSource={scheduleData.planner} columns={columns} rowKey="forecast_time_ist" pagination={false} />
      </Card>
    </div>
  );
};
