import React, { useEffect, useState } from 'react';
import { Card, Typography, Descriptions } from 'antd';

const { Title, Text } = Typography;

export const CapitalAllocation: React.FC = () => {
    const [allocationData, setAllocationData] = useState<any>(null);

    useEffect(() => {
        fetch('/api/v1/portfolio_intelligence/allocation')
            .then(res => res.json())
            .then(data => setAllocationData(data))
            .catch(err => console.error(err));
    }, []);

    return (
        <div style={{ padding: 24 }}>
            <Title level={2}>Capital Allocation Engine</Title>
            <Text type="secondary">Recommended position sizing and optimal capital distribution.</Text>

            <Card style={{ marginTop: 24 }}>
                <Descriptions bordered column={2}>
                    <Descriptions.Item label="Recommended Position Size">
                        ${allocationData?.recommended_position_size?.toLocaleString() || 'Loading...'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Max Risk per Trade">
                        ${allocationData?.max_risk_amount?.toLocaleString() || 'Loading...'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Total Allocated Capital">
                        ${allocationData?.total_allocated_capital?.toLocaleString() || 'Loading...'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Expected Portfolio Return">
                        <Text type="success">${allocationData?.expected_portfolio_return?.toLocaleString() || 'Loading...'}</Text>
                    </Descriptions.Item>
                </Descriptions>
            </Card>
        </div>
    );
};
