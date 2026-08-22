import React, { useEffect, useState } from 'react';
import { Card, Typography, Row, Col, Statistic, Progress, Spin, Alert, Table, List } from 'antd';
import { SafetyOutlined, WarningOutlined, FundProjectionScreenOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;

export const ForecastValidation: React.FC = () => {
  const [calibration, setCalibration] = useState<any>(null);
  const [drift, setDrift] = useState<any>(null);
  const [improvement, setImprovement] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchValidation = async () => {
      try {
        const [calRes, driftRes, impRes] = await Promise.all([
          fetch('/api/v1/validation/calibration'),
          fetch('/api/v1/validation/drift'),
          fetch('/api/v1/validation/improvement')
        ]);
        setCalibration(await calRes.json());
        setDrift(await driftRes.json());
        setImprovement(await impRes.json());
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchValidation();
  }, []);

  if (loading) return <Spin size="large" className="flex justify-center mt-20" />;

  const calibrationColumns = [
    { title: 'Confidence Bucket', dataIndex: 'confidence_range', key: 'confidence_range' },
    { title: 'Empirical Accuracy', dataIndex: 'actual_accuracy', key: 'actual_accuracy', render: (val: number) => `${(val * 100).toFixed(1)}%` },
    { title: 'Samples', dataIndex: 'samples', key: 'samples' },
  ];

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center space-x-3 border-b border-gray-700 pb-4">
        <SafetyOutlined className="text-3xl text-green-400" />
        <Title level={2} className="!mb-0 text-gray-100">Forecast Validation & Calibration</Title>
      </div>

      {drift && drift.drift_detected && (
        <Alert
          message="Model Drift Detected"
          description={`${drift.alert} ${drift.recommendation}`}
          type="error"
          showIcon
          icon={<WarningOutlined />}
          className="bg-red-900 border-red-700 text-red-100"
        />
      )}

      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="Confidence Calibration" className="bg-gray-800 border-gray-700 h-full">
            <Statistic title="Overall Calibration Score" value={calibration?.calibration_score * 100} suffix="%" />
            <Text className="text-gray-400 block mb-4">{calibration?.conclusion}</Text>
            <Table 
              columns={calibrationColumns} 
              dataSource={(calibration?.buckets || []).map((b: any, i: number) => ({ ...b, key: i }))} 
              pagination={false} 
              size="small"
              className="dark-theme-table"
            />
          </Card>
        </Col>

        <Col span={12}>
          <Card title="Continuous Improvement Engine" className="bg-gray-800 border-gray-700 h-full" extra={<FundProjectionScreenOutlined className="text-blue-400" />}>
            <List
              itemLayout="horizontal"
              dataSource={improvement ? Object.entries(improvement) : []}
              renderItem={(item: any) => (
                <List.Item>
                  <List.Item.Meta
                    title={<span className="text-gray-200 capitalize">{item[0].replace(/_/g, ' ')}</span>}
                    description={<span className="text-gray-400">{item[1]}</span>}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};
