import React from 'react';
import { Card, Button, Slider } from 'antd';
import { Play, Pause, FastForward } from 'lucide-react';

export const HistoricalReplay: React.FC = () => {
  return (
    <div className="p-4 space-y-4">
      <h1 className="text-xl font-bold">Historical Replay Engine</h1>
      <Card title="Playback Controls">
        <div className="flex items-center gap-4">
          <Button icon={<Play className="w-4 h-4" />}>Start</Button>
          <Button icon={<Pause className="w-4 h-4" />}>Pause</Button>
          <Button icon={<FastForward className="w-4 h-4" />}>Step</Button>
        </div>
        <div className="mt-6">
          <p>Playback Speed (x)</p>
          <Slider min={1} max={100} defaultValue={1} marks={{1: '1x', 10: '10x', 50: '50x', 100: '100x'}} />
        </div>
      </Card>
    </div>
  );
};
