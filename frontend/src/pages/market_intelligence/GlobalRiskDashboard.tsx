import React from 'react';
import { Card, Typography, Row, Col, Statistic, Progress } from 'antd';

const { Title, Text } = Typography;

export const GlobalRiskDashboard: React.FC = () => {
    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>Global Risk Dashboard</Title>
            <Text type="secondary">Consolidated view of all active risk parameters across the portfolio.</Text>

            <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
                <Col span={8}>
                    <Card>
                        <Statistic title="Total Margin Used" value={15.4} suffix="%" />
                        <div style={{ marginTop: 16 }}>
                            <Text>Margin Level</Text>
                            <Progress percent={85} strokeColor="#52c41a" />
                        </div>
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic title="Average Confidence" value={89} suffix="%" />
                        <div style={{ marginTop: 16 }}>
                            <Text>Portfolio Quality</Text>
                            <Progress percent={89} strokeColor="#1890ff" />
                        </div>
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic title="Max Drawdown Risk" value={4.2} suffix="%" valueStyle={{ color: '#cf1322' }} />
                        <div style={{ marginTop: 16 }}>
                            <Text>Risk Limit (10%)</Text>
                            <Progress percent={42} strokeColor="#faad14" />
                        </div>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};
