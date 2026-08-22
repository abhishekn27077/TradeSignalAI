import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Typography, Statistic, Table, Tag } from 'antd';
import { Area } from '@ant-design/plots';

const { Title, Text } = Typography;

export const MarketCommandCenter: React.FC = () => {
    const [commandData, setCommandData] = useState<any>(null);

    useEffect(() => {
        // Fetch data from API
        fetch('/api/v1/portfolio_intelligence/market-rotation')
            .then(res => res.json())
            .then(data => setCommandData(data))
            .catch(err => console.error(err));
    }, []);

    // Placeholder data for chart
    const data = [
        { time: '08:00', value: 3 },
        { time: '10:00', value: 4 },
        { time: '12:00', value: 3.5 },
        { time: '14:00', value: 5 },
        { time: '16:00', value: 4.9 },
    ];

    const config = {
        data,
        xField: 'time',
        yField: 'value',
        height: 200,
        smooth: true,
        areaStyle: { fill: 'l(270) 0:#ffffff 0.5:#7ec2f3 1:#1890ff' }
    };

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>Market Command Center</Title>
            <Text type="secondary">Central overview of global market health and intelligence.</Text>

            <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
                <Col span={6}>
                    <Card>
                        <Statistic title="Market Regime" value={commandData?.regime || 'Loading...'} valueStyle={{ color: '#3f8600' }} />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic title="Active Opportunities" value={12} />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic title="Market Health Score" value={88} suffix="/ 100" />
                    </Card>
                </Col>
                <Col span={6}>
                    <Card>
                        <Statistic title="Global Risk Level" value="Moderate" />
                    </Card>
                </Col>
            </Row>

            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                <Col span={16}>
                    <Card title="Market Volatility (24h)">
                        <Area {...config} />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card title="Top AI Opportunities">
                        <p><Tag color="green">BUY</Tag> <b>BTC/USD</b> (95% Conf)</p>
                        <p><Tag color="green">BUY</Tag> <b>ETH/USD</b> (92% Conf)</p>
                        <p><Tag color="red">SELL</Tag> <b>USD/JPY</b> (88% Conf)</p>
                        <p><Tag color="red">SELL</Tag> <b>EUR/GBP</b> (85% Conf)</p>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};
