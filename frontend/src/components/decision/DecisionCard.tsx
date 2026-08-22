import React from 'react';

interface DecisionProps {
  grade: string;
  score: number;
  confidence: number;
  rrRatio: number;
  approved: boolean;
  reasons: string[];
  warnings: string[];
}

export const DecisionCard: React.FC<DecisionProps> = ({
  grade, score, confidence, rrRatio, approved, reasons, warnings
}) => {
  const getGradeColor = (grade: string) => {
    if (grade === "A+") return "text-green-500";
    if (grade === "A") return "text-emerald-400";
    if (grade === "B") return "text-yellow-400";
    if (grade === "C") return "text-orange-400";
    return "text-red-500";
  };

  return (
    <div className={`p-4 rounded-xl border ${approved ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-bold text-gray-100">Decision Intelligence</h3>
          <p className="text-sm text-gray-400">Trade Qualification: {approved ? 'APPROVED' : 'REJECTED'}</p>
        </div>
        <div className={`text-4xl font-black ${getGradeColor(grade)}`}>
          {grade}
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="p-3 bg-gray-800 rounded-lg">
          <div className="text-xs text-gray-400">Qual. Score</div>
          <div className="text-lg font-semibold text-white">{score.toFixed(1)}/100</div>
        </div>
        <div className="p-3 bg-gray-800 rounded-lg">
          <div className="text-xs text-gray-400">Confidence</div>
          <div className="text-lg font-semibold text-white">{(confidence * 100).toFixed(1)}%</div>
        </div>
        <div className="p-3 bg-gray-800 rounded-lg">
          <div className="text-xs text-gray-400">R:R Ratio</div>
          <div className="text-lg font-semibold text-white">{rrRatio.toFixed(2)}</div>
        </div>
      </div>

      <div className="space-y-2 text-sm">
        {reasons.length > 0 && (
          <div>
            <div className="text-green-400 font-semibold mb-1">Strengths</div>
            <ul className="list-disc list-inside text-gray-300">
              {reasons.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        )}
        {warnings.length > 0 && (
          <div className="mt-2">
            <div className="text-red-400 font-semibold mb-1">Warnings & Risks</div>
            <ul className="list-disc list-inside text-gray-300">
              {warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};
