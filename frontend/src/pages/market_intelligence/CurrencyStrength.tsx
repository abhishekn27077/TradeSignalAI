import React, { useEffect, useState } from 'react';
import { Card, Table, Typography, Tag, Progress } from 'antd';

const { Title, Text } = Typography;

export const CurrencyStrength: React.FC = () => {
    const [strengthData, setStrengthData] = useState<any>(null);

    useEffect(() => {
        fetch('/api/v1/portfolio_intelligence/currency-strength')
            .then(res => res.json())
            .then(data => setStrengthData(data))
            .catch(err => console.error(err));
    }, []);

    const columns = [
        { title: 'Currency', dataIndex: 'currency', key: 'currency', render: (text: string) => <b>{text}</b> },
        { title: 'Strength', dataIndex: 'strength', key: 'strength', render: (val: number) => <Progress percent={val * 100} showInfo={false} /> },
        { title: 'Trend', dataIndex: 'trend', key: 'trend', render: (text: string) => <Tag color={text.includes('Bullish') ? 'green' : (text.includes('Bearish') ? 'red' : 'blue')}>{text}</Tag> },
        { title: 'Momentum', dataIndex: 'momentum', key: 'momentum', render: (val: number) => <Text type={val > 0 ? 'success' : 'danger'}>{val > 0 ? `+${val}` : val}</Text> }
    ];

    const data = strengthData ? Object.keys(strengthData).map(k => ({
        key: k,
        currency: k,
        ...strengthData[k]
    })).sort((a, b) => b.strength - a.strength) : [];

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>Currency Strength Engine</Title>
            <Text type="secondary">Relative strength rankings and momentum across major currencies.</Text>

            <Card style={{ marginTop: 24 }}>
                <Table columns={columns} dataSource={data} pagination={false} />
            </Card>
        </div>
    );
};
