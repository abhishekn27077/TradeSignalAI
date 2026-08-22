import React, { useState } from 'react';
import { Calendar } from 'lucide-react';

export type DateRangePreset = 'today' | 'yesterday' | '7d' | '30d' | 'all' | 'custom';

export interface DateFilterValue {
  preset: DateRangePreset;
  startDate?: string; // YYYY-MM-DD
  endDate?: string;   // YYYY-MM-DD
}

interface DateSelectorProps {
  value: DateFilterValue;
  onChange: (val: DateFilterValue) => void;
}

export const DateSelector: React.FC<DateSelectorProps> = ({ value, onChange }) => {
  const [customOpen, setCustomOpen] = useState(value.preset === 'custom');
  const [startInput, setStartInput] = useState(value.startDate || '');
  const [endInput, setEndInput] = useState(value.endDate || '');

  const presets: { key: DateRangePreset; label: string }[] = [
    { key: 'today', label: 'Today' },
    { key: 'yesterday', label: 'Yesterday' },
    { key: '7d', label: '7 Days' },
    { key: '30d', label: '30 Days' },
    { key: 'all', label: 'All History' },
    { key: 'custom', label: 'Custom' },
  ];

  const handlePresetSelect = (preset: DateRangePreset) => {
    if (preset === 'custom') {
      setCustomOpen(true);
      onChange({ preset: 'custom', startDate: startInput, endDate: endInput });
    } else {
      setCustomOpen(false);
      onChange({ preset });
    }
  };

  const applyCustomRange = () => {
    if (startInput && endInput) {
      onChange({ preset: 'custom', startDate: startInput, endDate: endInput });
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      {/* Preset Pills */}
      <div className="flex bg-trading-surface border border-panel-border rounded-lg p-0.5">
        {presets.map((p) => {
          const active = value.preset === p.key;
          return (
            <button
              key={p.key}
              onClick={() => handlePresetSelect(p.key)}
              className={`px-3 py-1 text-[11px] font-medium rounded-md transition-colors ${
                active
                  ? 'bg-accent-blue/15 text-accent-blue font-semibold shadow-sm'
                  : 'text-text-muted hover:text-text-primary hover:bg-trading-hover/50'
              }`}
            >
              {p.label}
            </button>
          );
        })}
      </div>

      {/* Custom Date Inputs if custom is selected */}
      {(customOpen || value.preset === 'custom') && (
        <div className="flex items-center gap-1.5 bg-trading-surface border border-panel-border rounded-lg px-2.5 py-1 text-[11px]">
          <Calendar className="w-3.5 h-3.5 text-text-muted" />
          <input
            type="date"
            value={startInput}
            onChange={(e) => {
              setStartInput(e.target.value);
            }}
            className="bg-transparent text-text-primary focus:outline-none text-[11px] cursor-pointer"
          />
          <span className="text-text-muted">to</span>
          <input
            type="date"
            value={endInput}
            onChange={(e) => {
              setEndInput(e.target.value);
            }}
            className="bg-transparent text-text-primary focus:outline-none text-[11px] cursor-pointer"
          />
          <button
            onClick={applyCustomRange}
            disabled={!startInput || !endInput}
            className="px-2 py-0.5 rounded bg-accent-blue/20 text-accent-blue hover:bg-accent-blue/30 disabled:opacity-40 text-[10px] font-semibold transition-colors"
          >
            Apply
          </button>
        </div>
      )}
    </div>
  );
};
