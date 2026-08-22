import React from 'react';
import { Card, Table, Tag } from 'antd';

export const ModelLeaderboard: React.FC = () => {
  const columns = [
    { title: 'Rank', dataIndex: 'rank', key: 'rank' },
    { title: 'Model', dataIndex: 'model', key: 'model' },
    { title: 'Accuracy', dataIndex: 'accuracy', key: 'accuracy' },
    { title: 'Profitability', dataIndex: 'profitability', key: 'profitability' },
    { title: 'Status', key: 'status', render: () => <Tag color="green">Active</Tag> }
  ];

  const data = [
    { key: '1', rank: 1, model: 'Kronos', accuracy: '72.5%', profitability: 1.8 },
    { key: '2', rank: 2, model: 'Transformer', accuracy: '68.2%', profitability: 1.4 },
    { key: '3', rank: 3, model: 'LSTM', accuracy: '65.1%', profitability: 1.1 },
    { key: '4', rank: 4, model: 'XGBoost', accuracy: '60.5%', profitability: 0.9 },
  ];

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold">Model Leaderboard</h1>
      <Card>
        <Table columns={columns} dataSource={data} pagination={false} />
      </Card>
    </div>
  );
};
