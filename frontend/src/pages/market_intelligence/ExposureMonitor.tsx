import React, { useEffect, useState } from 'react';
import { Card, Typography, List, Alert, Progress } from 'antd';

const { Title, Text } = Typography;

export const ExposureMonitor: React.FC = () => {
    const [exposureData, setExposureData] = useState<any>(null);

    useEffect(() => {
        fetch('/api/v1/portfolio_intelligence/exposure')
            .then(res => res.json())
            .then(data => setExposureData(data))
            .catch(err => console.error(err));
    }, []);

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>Exposure Monitor</Title>
            <Text type="secondary">Detects concentration risks and duplicate signals.</Text>

            <Card style={{ marginTop: 24 }}>
                <Title level={4}>Total Exposure</Title>
                <Progress percent={exposureData?.total_exposure_pct || 0} status={exposureData?.total_exposure_pct > 80 ? "exception" : "normal"} />

                <Title level={4} style={{ marginTop: 24 }}>Warnings</Title>
                <List
                    dataSource={exposureData?.warnings || []}
                    renderItem={(item: string) => (
                        <List.Item>
                            <Alert message={item} type="warning" showIcon style={{ width: '100%' }} />
                        </List.Item>
                    )}
                />
            </Card>
        </div>
    );
};
