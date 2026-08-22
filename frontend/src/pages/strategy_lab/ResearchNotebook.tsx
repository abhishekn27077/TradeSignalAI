import React, { useEffect, useState } from 'react';

const ResearchNotebook: React.FC = () => {
    const [notebooks, setNotebooks] = useState<any[]>([]);

    useEffect(() => {
        fetch('http://localhost:8000/api/v1/strategy-lab/notebook')
            .then(res => res.json())
            .then(data => setNotebooks(data))
            .catch(err => console.error(err));
    }, []);

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4 text-white">Research Notebook</h1>
            <div className="grid grid-cols-1 gap-6">
                {notebooks.map((nb: any) => (
                    <div key={nb.id} className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                        <h3 className="text-xl font-bold text-white mb-2">{nb.id}</h3>
                        <p className="text-gray-400 mb-2"><strong>Hypothesis:</strong> {nb.hypothesis}</p>
                        <p className="text-gray-400 mb-2"><strong>Results:</strong> {nb.results}</p>
                        <p className="text-gray-400"><strong>Recommendations:</strong> {nb.recommendations}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ResearchNotebook;
