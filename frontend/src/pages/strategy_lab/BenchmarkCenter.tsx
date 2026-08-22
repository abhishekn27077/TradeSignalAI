import React, { useEffect, useState } from 'react';

const BenchmarkCenter: React.FC = () => {
    const [leaderboard, setLeaderboard] = useState<any[]>([]);

    useEffect(() => {
        fetch('http://localhost:8000/api/v1/strategy-lab/benchmarks')
            .then(res => res.json())
            .then(data => setLeaderboard(data.leaderboard))
            .catch(err => console.error(err));
    }, []);

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4 text-white">Benchmark Center</h1>
            <table className="w-full text-left text-gray-300">
                <thead>
                    <tr className="bg-gray-800">
                        <th className="p-3 border-b border-gray-700">Strategy</th>
                        <th className="p-3 border-b border-gray-700">Sharpe Ratio</th>
                        <th className="p-3 border-b border-gray-700">Win Rate</th>
                    </tr>
                </thead>
                <tbody>
                    {leaderboard.map((l: any, idx: number) => (
                        <tr key={idx} className="border-b border-gray-700">
                            <td className="p-3">{l.strategy}</td>
                            <td className="p-3 text-green-400">{l.sharpe}</td>
                            <td className="p-3 text-blue-400">{l.win_rate}%</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default BenchmarkCenter;
