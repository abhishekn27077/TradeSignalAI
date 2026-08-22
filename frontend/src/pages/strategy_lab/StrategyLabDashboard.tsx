import React from 'react';

const StrategyLabDashboard: React.FC = () => {
    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4 text-white">AI Strategy Laboratory</h1>
            <p className="text-gray-400 mb-8">Central Research Workspace</p>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <h3 className="text-gray-400 text-sm font-medium">Active Strategies</h3>
                    <p className="text-3xl font-bold text-green-400 mt-2">12</p>
                </div>
                <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <h3 className="text-gray-400 text-sm font-medium">Candidate Strategies</h3>
                    <p className="text-3xl font-bold text-blue-400 mt-2">5</p>
                </div>
                <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <h3 className="text-gray-400 text-sm font-medium">Experimental Strategies</h3>
                    <p className="text-3xl font-bold text-yellow-400 mt-2">18</p>
                </div>
                <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                    <h3 className="text-gray-400 text-sm font-medium">Retired Strategies</h3>
                    <p className="text-3xl font-bold text-red-400 mt-2">45</p>
                </div>
            </div>
        </div>
    );
};

export default StrategyLabDashboard;
