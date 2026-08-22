import React, { useEffect, useState } from 'react';
import { Card, Typography, Statistic, Row, Col } from 'antd';

const { Title, Text } = Typography;

export const SectorRotation: React.FC = () => {
    const [rotationData, setRotationData] = useState<any>(null);

    useEffect(() => {
        fetch('/api/v1/portfolio_intelligence/market-rotation')
            .then(res => res.json())
            .then(data => setRotationData(data))
            .catch(err => console.error(err));
    }, []);

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>Sector & Market Rotation</Title>
            <Text type="secondary">Detect capital flows across major asset classes and risk regimes.</Text>

            <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
                <Col span={8}>
                    <Card>
                        <Statistic title="Current Market Regime" value={rotationData?.regime || 'Loading...'} valueStyle={{ color: '#eb2f96' }} />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic title="Capital Flow Priority" value={rotationData?.capital_flow || 'Loading...'} />
                    </Card>
                </Col>
                <Col span={8}>
                    <Card>
                        <Statistic title="Sector Leadership" value={rotationData?.sector_rotation || 'Loading...'} />
                    </Card>
                </Col>
            </Row>
        </div>
    );
};
