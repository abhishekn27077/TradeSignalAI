import React from 'react';

export const DailyOutlook: React.FC = () => {
  return (
    <div className="p-6 h-full flex flex-col">
      <h1 className="text-2xl font-bold mb-4">Daily Outlook</h1>
      <p className="text-text-secondary">Summary of the day's market bias and strongest assets.</p>
    </div>
  );
};
