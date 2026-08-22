import React from 'react';
import { Modal, Tabs, Descriptions, Timeline, Progress, List, Tag } from 'antd';

interface PredictionDetailModalProps {
  visible: boolean;
  onClose: () => void;
  prediction: any;
}

export const PredictionDetailModal: React.FC<PredictionDetailModalProps> = ({ visible, onClose, prediction }) => {
  if (!prediction) return null;

  const items = [
    {
      key: '1',
      label: 'Explainability',
      children: (
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Why">{prediction.explainability_data?.why_direction}</Descriptions.Item>
          <Descriptions.Item label="Market Regime">{prediction.explainability_data?.market_regime}</Descriptions.Item>
          <Descriptions.Item label="Risk Factors">{prediction.explainability_data?.risk_factors?.join(', ')}</Descriptions.Item>
        </Descriptions>
      )
    },
    {
      key: '2',
      label: 'Confidence Breakdown',
      children: (
        <List
          dataSource={Object.entries(prediction.confidence_breakdown || {})}
          renderItem={([key, val]: any) => (
            <List.Item>
              <div style={{ width: '100%' }}>
                <span>{key}</span>
                <Progress percent={Math.round(val * 100)} size="small" />
              </div>
            </List.Item>
          )}
        />
      )
    },
    {
      key: '3',
      label: 'Agreement Matrix',
      children: (
        <div>
          <Progress type="dashboard" percent={prediction.agreement_matrix?.agreement_percentage} />
          <p>Consensus Agreement</p>
        </div>
      )
    },
    {
      key: '4',
      label: 'Timeline',
      children: (
        <Timeline
          items={(prediction.timeline_events || []).map((e: any) => ({
            children: (
              <>
                <p><b>{e.state}</b></p>
                <p>{new Date(e.timestamp).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' })}</p>
              </>
            ),
            color: e.state === 'ACTIVE' ? 'green' : 'blue'
          }))}
        />
      )
    }
  ];

  return (
    <Modal
      title={`Forecast Detail: ${prediction.symbol} (${prediction.quality_grade || 'U'})`}
      open={visible}
      onCancel={onClose}
      footer={null}
      width={700}
    >
      <Tabs defaultActiveKey="1" items={items} />
    </Modal>
  );
};
