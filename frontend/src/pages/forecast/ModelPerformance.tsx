import React, { useEffect, useState } from 'react';
import { Card, Typography, Row, Col, Spin, Table, Tag } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

export const ModelPerformance: React.FC = () => {
  const [sessionData, setSessionData] = useState<any>(null);
  const [regimeData, setRegimeData] = useState<any>(null);
  const [holdTimeData, setHoldTimeData] = useState<any>(null);
  const [pairData, setPairData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        const [sessRes, regRes, holdRes, pairRes] = await Promise.all([
          fetch('/api/v1/validation/session'),
          fetch('/api/v1/validation/regime'),
          fetch('/api/v1/validation/hold-time'),
          fetch('/api/v1/validation/pair-analysis')
        ]);
        setSessionData(await sessRes.json());
        setRegimeData(await regRes.json());
        setHoldTimeData(await holdRes.json());
        setPairData(await pairRes.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchPerformance();
  }, []);

  if (loading) return <Spin size="large" className="flex justify-center mt-20" />;

  const pairColumns = [
    { title: 'Symbol', dataIndex: 'symbol', key: 'symbol', render: (t: string) => <strong className="text-white">{t}</strong> },
    { title: 'Accuracy', dataIndex: 'accuracy', key: 'accuracy', render: (v: number) => `${(v * 100).toFixed(1)}%` },
    { title: 'Profitability', dataIndex: 'profitability', key: 'profitability' },
    { 
      title: 'Risk', 
      dataIndex: 'risk', 
      key: 'risk',
      render: (risk: string) => {
        let color = risk === 'High' ? 'red' : risk === 'Medium' ? 'orange' : 'green';
        return <Tag color={color}>{risk}</Tag>;
      }
    },
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center space-x-3 border-b border-gray-700 pb-4">
        <BarChartOutlined className="text-3xl text-indigo-400" />
        <Title level={2} className="!mb-0 text-gray-100">Model Performance Analytics</Title>
      </div>

      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="Session Validation" className="bg-gray-800 border-gray-700 h-full">
            <ul className="space-y-4">
              {sessionData && Object.keys(sessionData).map((s) => (
                <li key={s} className="flex justify-between border-b border-gray-700 pb-2">
                  <span className="capitalize font-semibold text-gray-300">{s.replace('_', ' ')}</span>
                  <span>Accuracy: {(sessionData[s].accuracy * 100).toFixed(1)}% | Vol: {sessionData[s].volume}</span>
                </li>
              ))}
            </ul>
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="Regime Validation" className="bg-gray-800 border-gray-700 h-full">
            <ul className="space-y-4">
              {regimeData && Object.keys(regimeData).map((r) => (
                <li key={r} className="flex justify-between border-b border-gray-700 pb-2">
                  <span className="capitalize font-semibold text-gray-300">{r.replace('_', ' ')}</span>
                  <span>Accuracy: {(regimeData[r].accuracy * 100).toFixed(1)}% | PF: {regimeData[r].profit_factor}</span>
                </li>
              ))}
            </ul>
          </Card>
        </Col>
        
        <Col span={12}>
          <Card title="Pair Analysis Ranking" className="bg-gray-800 border-gray-700 h-full">
             <Table 
                columns={pairColumns} 
                dataSource={pairData.map((d, i) => ({ ...d, key: i }))} 
                pagination={false} 
                size="small"
                className="dark-theme-table"
              />
          </Card>
        </Col>

        <Col span={12}>
          <Card title="Hold-Time Analysis" className="bg-gray-800 border-gray-700 h-full">
             {holdTimeData && (
                <>
                  <div className="mb-4">
                    <Text className="text-gray-400">Optimal Hold Time: </Text>
                    <Tag color="purple" className="text-lg">{holdTimeData.optimal_hold_time.replace('_', ' ').toUpperCase()}</Tag>
                  </div>
                  <ul className="space-y-2">
                    {Object.keys(holdTimeData).filter(k => k !== 'optimal_hold_time').map((h) => (
                      <li key={h} className="flex justify-between border-b border-gray-700 pb-1">
                        <span className="capitalize text-gray-300">{h.replace('_', ' ')}</span>
                        <span>Accuracy: {(holdTimeData[h].accuracy * 100).toFixed(1)}%</span>
                      </li>
                    ))}
                  </ul>
                </>
             )}
          </Card>
        </Col>
      </Row>
    </div>
  );
};
