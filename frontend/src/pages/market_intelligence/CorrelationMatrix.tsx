import React, { useEffect, useState } from 'react';
import { Card, Table, Typography, Tag } from 'antd';

const { Title, Text } = Typography;

export const CorrelationMatrix: React.FC = () => {
    const [correlationData, setCorrelationData] = useState<any>(null);

    useEffect(() => {
        fetch('/api/v1/portfolio_intelligence/correlation')
            .then(res => res.json())
            .then(data => setCorrelationData(data))
            .catch(err => console.error(err));
    }, []);

    const columns = [
        { title: 'Pair 1', dataIndex: 'pair_1', key: 'pair_1' },
        { title: 'Pair 2', dataIndex: 'pair_2', key: 'pair_2' },
        { title: 'Correlation', dataIndex: 'correlation', key: 'correlation', render: (val: number) => (
            <Tag color={val > 0.8 ? 'green' : (val < -0.8 ? 'red' : 'blue')}>
                {val.toFixed(2)}
            </Tag>
        )},
    ];

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>Correlation Engine</Title>
            <Text type="secondary">Real-time positive and negative rolling correlations.</Text>

            <div style={{ display: 'flex', gap: '24px', marginTop: 24 }}>
                <Card title="Highly Positively Correlated" style={{ flex: 1 }}>
                    <Table columns={columns} dataSource={correlationData?.positive || []} pagination={false} rowKey="pair_1" />
                </Card>
                
                <Card title="Highly Negatively Correlated" style={{ flex: 1 }}>
                    <Table columns={columns} dataSource={correlationData?.negative || []} pagination={false} rowKey="pair_1" />
                </Card>
            </div>
        </div>
    );
};
