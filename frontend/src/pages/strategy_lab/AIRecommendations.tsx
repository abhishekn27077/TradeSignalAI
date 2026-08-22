import React, { useEffect, useState } from 'react';

const AIRecommendations: React.FC = () => {
    const [recs, setRecs] = useState<any[]>([]);

    useEffect(() => {
        fetch('http://localhost:8000/api/v1/strategy-lab/recommendations')
            .then(res => res.json())
            .then(data => setRecs(data))
            .catch(err => console.error(err));
    }, []);

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4 text-white">AI Recommendations</h1>
            <div className="grid grid-cols-1 gap-6">
                {recs.map((rec: any, idx: number) => (
                    <div key={idx} className={`p-6 rounded-lg border ${rec.action === 'Retire' ? 'bg-red-900 border-red-700' : 'bg-blue-900 border-blue-700'}`}>
                        <h3 className="text-xl font-bold text-white mb-2">{rec.action}: {rec.target}</h3>
                        <p className="text-gray-300">{rec.reason}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default AIRecommendations;
