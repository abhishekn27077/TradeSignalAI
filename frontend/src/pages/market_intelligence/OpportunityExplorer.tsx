import React from 'react';
import { Card, Typography, Table, Tag } from 'antd';

const { Title, Text } = Typography;

export const OpportunityExplorer: React.FC = () => {
    // Stub data
    const dataSource = [
        { key: '1', symbol: 'BTCUSD', type: 'LONG', conf: 95, rr: 3.5, regime: 'Trending' },
        { key: '2', symbol: 'EURUSD', type: 'SHORT', conf: 88, rr: 2.1, regime: 'Sideways' },
    ];

    const columns = [
        { title: 'Symbol', dataIndex: 'symbol', key: 'symbol' },
        { title: 'Type', dataIndex: 'type', key: 'type', render: (val: string) => <Tag color={val === 'LONG' ? 'green' : 'red'}>{val}</Tag> },
        { title: 'Confidence', dataIndex: 'conf', key: 'conf', render: (val: number) => `${val}%` },
        { title: 'R:R', dataIndex: 'rr', key: 'rr' },
        { title: 'Regime', dataIndex: 'regime', key: 'regime' },
    ];

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>Opportunity Explorer</Title>
            <Text type="secondary">Filter and explore all generated forecasts across the entire market.</Text>

            <Card style={{ marginTop: 24 }}>
                <Table columns={columns} dataSource={dataSource} />
            </Card>
        </div>
    );
};
