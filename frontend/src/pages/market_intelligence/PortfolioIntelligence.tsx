import React from 'react';
import { Card, Typography, Row, Col, Statistic, Progress } from 'antd';

const { Title, Text } = Typography;

export const PortfolioIntelligence: React.FC = () => {
    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>Portfolio Intelligence</Title>
            <Text type="secondary">Holistic view of portfolio risk, exposure, and expected drawdown.</Text>

            <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
                <Col span={8}>
                    <Card>
                        <Statistic title="Portfolio Risk" value={2.5} suffix="%" valueStyle={{ color: '#cf1322' }} />
                        <div style={{ marginTop: 16 }}>
                            <Text>Diversification Score</Text>
                            <Progress percent={85} strokeColor="#52c41a" />
                        </div>
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic title="Expected Drawdown" value={8.2} suffix="%" />
                        <div style={{ marginTop: 16 }}>
                            <Text>Correlation Risk</Text>
                            <Progress percent={40} strokeColor="#faad14" />
                        </div>
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic title="Total Exposure" value={50} suffix="%" />
                    </Card>
                </Col>
            </Row>
        </div>
    );
};
