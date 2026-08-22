import React from 'react';

const ExperimentManager: React.FC = () => {
    return (
        <div className="p-6">
            <h1 className="text-2xl font-bold mb-4 text-white">Experiment Manager</h1>
            <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
                <p className="text-gray-400">Track and manage active quantitative experiments.</p>
                {/* Real-time experiment status would go here */}
            </div>
        </div>
    );
};

export default ExperimentManager;
