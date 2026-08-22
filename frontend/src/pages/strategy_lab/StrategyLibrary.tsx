import React, { useEffect, useState } from 'react';

const StrategyLibrary: React.FC = () => {
    const [strategies, setStrategies] = useState<any[]>([]);

    useEffect(() => {
        fetch('/api/v1/strategies')
            .then(res => res.json())
            .then(data => setStrategies(data.strategies || []))
            .catch(err => console.error(err));
    }, []);

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4 text-white">Strategy Library</h1>
            <table className="w-full text-left text-gray-300">
                <thead>
                    <tr className="bg-gray-800">
                        <th className="p-3 border-b border-gray-700">ID</th>
                        <th className="p-3 border-b border-gray-700">Name</th>
                        <th className="p-3 border-b border-gray-700">Version</th>
                        <th className="p-3 border-b border-gray-700">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {strategies.map((s: any, index: number) => (
                        <tr key={s.name || index} className="border-b border-gray-700">
                            <td className="p-3">{index + 1}</td>
                            <td className="p-3">{s.name}</td>
                            <td className="p-3">{s.version}</td>
                            <td className="p-3">
                                <span className="bg-blue-900 text-blue-300 px-2 py-1 rounded text-xs">
                                    {s.status}
                                </span>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default StrategyLibrary;
