import React, { useEffect, useState } from 'react';

const FeatureImportance: React.FC = () => {
    const [features, setFeatures] = useState<any[]>([]);

    useEffect(() => {
        fetch('http://localhost:8000/api/v1/strategy-lab/features')
            .then(res => res.json())
            .then(data => setFeatures(data))
            .catch(err => console.error(err));
    }, []);

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4 text-white">Feature Importance</h1>
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                {features.map((f: any) => (
                    <div key={f.feature} className="mb-4">
                        <div className="flex justify-between text-gray-300 mb-1">
                            <span>{f.feature}</span>
                            <span>{f.importance * 100}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded h-2">
                            <div className="bg-blue-500 h-2 rounded" style={{ width: `${f.importance * 100}%` }}></div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default FeatureImportance;
