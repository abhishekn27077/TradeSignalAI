import React, { useState } from 'react';

const StrategyBuilder: React.FC = () => {
    const [config, setConfig] = useState({ indicator: 'RSI', risk: '1%' });

    const handleCompile = async () => {
        // Compile config
        alert('Strategy compiled and sent to evaluation queue.');
    };

    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4 text-white">Visual Strategy Builder</h1>
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <div className="mb-4">
                    <label className="block text-gray-400 mb-2">Indicator</label>
                    <select className="w-full bg-gray-900 border border-gray-700 p-2 rounded text-white">
                        <option>RSI</option>
                        <option>MACD</option>
                        <option>EMA</option>
                    </select>
                </div>
                <div className="mb-4">
                    <label className="block text-gray-400 mb-2">Market Structure</label>
                    <select className="w-full bg-gray-900 border border-gray-700 p-2 rounded text-white">
                        <option>Order Blocks</option>
                        <option>Liquidity Zones</option>
                    </select>
                </div>
                <button 
                    onClick={handleCompile}
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
                >
                    Compile Strategy
                </button>
            </div>
        </div>
    );
};

export default StrategyBuilder;
