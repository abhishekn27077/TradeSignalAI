import React from 'react';
import { Card, Button, Form, Input, InputNumber } from 'antd';

export const HyperparameterLab: React.FC = () => {
  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold">Hyperparameter Lab</h1>
      <Card title="New Experiment">
        <Form layout="vertical">
          <div className="grid grid-cols-2 gap-4">
            <Form.Item label="Experiment Name">
              <Input defaultValue="Exp-Alpha" />
            </Form.Item>
            <Form.Item label="Forecast Horizon (Candles)">
              <InputNumber className="w-full" defaultValue={10} />
            </Form.Item>
            <Form.Item label="Confidence Threshold">
              <InputNumber className="w-full" step={0.01} defaultValue={0.85} max={1} min={0} />
            </Form.Item>
            <Form.Item label="Features (Comma Separated)">
              <Input defaultValue="RSI, MACD, Volume" />
            </Form.Item>
          </div>
          <Button type="primary">Run Experiment</Button>
        </Form>
      </Card>
    </div>
  );
};
