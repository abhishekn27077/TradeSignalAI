import React from 'react';

export const Dashboard: React.FC = () => {
  return (
    <div className="p-6 h-full flex flex-col">
      <h1 className="text-2xl font-bold mb-4">Forecast Dashboard</h1>
      <p className="text-text-secondary">High-level view of active predictions, system health, and upcoming windows.</p>
    </div>
  );
};
