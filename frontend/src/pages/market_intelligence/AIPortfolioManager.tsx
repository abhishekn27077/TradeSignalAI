import React, { useEffect, useState } from 'react';
import { Card, Typography, List, Tag, Row, Col, Progress } from 'antd';

const { Title, Text } = Typography;

export const AIPortfolioManager: React.FC = () => {
    const [portfolioData, setPortfolioData] = useState<any>(null);

    useEffect(() => {
        fetch('/api/v1/portfolio_intelligence/portfolio')
            .then(res => res.json())
            .then(data => setPortfolioData(data))
            .catch(err => console.error(err));
    }, []);

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>AI Portfolio Manager</Title>
            <Text type="secondary">AI-constructed optimal portfolios maximizing expected return and minimizing correlation.</Text>

            <Card style={{ marginTop: 24 }}>
                <Title level={4}>Expected Portfolio Quality</Title>
                <Progress percent={portfolioData?.portfolio_expected_quality || 0} strokeColor="#722ed1" />

                <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
                    <Col span={8}>
                        <Card title="Top 5 Core Allocation" type="inner">
                            <List
                                dataSource={portfolioData?.top_5 || []}
                                renderItem={(item: any) => (
                                    <List.Item>
                                        <Text strong>{item.symbol}</Text>
                                        <Tag color="purple">Score: {item.score}</Tag>
                                    </List.Item>
                                )}
                            />
                        </Card>
                    </Col>
                    <Col span={8}>
                        <Card title="Top 10 Expanded" type="inner">
                            <List
                                dataSource={portfolioData?.top_10 || []}
                                renderItem={(item: any) => (
                                    <List.Item>
                                        <Text strong>{item.symbol}</Text>
                                        <Tag color="purple">Score: {item.score}</Tag>
                                    </List.Item>
                                )}
                            />
                        </Card>
                    </Col>
                    <Col span={8}>
                        <Card title="Top 20 Broad" type="inner">
                            <List
                                dataSource={portfolioData?.top_20 || []}
                                renderItem={(item: any) => (
                                    <List.Item>
                                        <Text strong>{item.symbol}</Text>
                                        <Tag color="purple">Score: {item.score}</Tag>
                                    </List.Item>
                                )}
                            />
                        </Card>
                    </Col>
                </Row>
            </Card>
        </div>
    );
};
