import React, { useEffect, useState } from 'react';
import { Prediction } from '@types/index';
import { apiClient } from '@api/client';
import { PredictionCard } from '@components/PredictionCard';
import { SystemStatusComponent } from '@components/SystemStatus';
import { RefreshCw, Play, StopCircle } from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [schedulerRunning, setSchedulerRunning] = useState(false);

  useEffect(() => {
    // Initial load would happen here
    // For now, we'll show empty state
  }, []);

  const handleRunPipeline = async () => {
    setLoading(true);
    try {
      const result = await apiClient.runPipeline();
      // In real app, would refetch predictions
      alert(`Pipeline executed: ${result.message}`);
    } catch (err) {
      setError('Failed to run pipeline');
    } finally {
      setLoading(false);
    }
  };

  const handleStartScheduler = async () => {
    try {
      await apiClient.startScheduler();
      setSchedulerRunning(true);
      alert('Scheduler started');
    } catch (err) {
      setError('Failed to start scheduler');
    }
  };

  const handleStopScheduler = async () => {
    try {
      await apiClient.stopScheduler();
      setSchedulerRunning(false);
      alert('Scheduler stopped');
    } catch (err) {
      setError('Failed to stop scheduler');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Stock Prediction Dashboard
          </h1>
          <p className="text-gray-600">
            Real-time predictions powered by sentiment analysis and machine learning
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* System Status */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">System Status</h2>
          <SystemStatusComponent />
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Actions</h2>
          <div className="flex flex-wrap gap-4">
            <button
              onClick={handleRunPipeline}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
            >
              <RefreshCw className="w-4 h-4" />
              Run Pipeline
            </button>

            <button
              onClick={handleStartScheduler}
              disabled={schedulerRunning}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
            >
              <Play className="w-4 h-4" />
              Start Scheduler
            </button>

            <button
              onClick={handleStopScheduler}
              disabled={!schedulerRunning}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400"
            >
              <StopCircle className="w-4 h-4" />
              Stop Scheduler
            </button>
          </div>
        </div>

        {/* Predictions Grid */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Latest Predictions
          </h2>
          {predictions.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {predictions.map((pred) => (
                <PredictionCard key={`${pred.ticker}-${pred.prediction_date}`} prediction={pred} />
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-md p-12 text-center">
              <p className="text-gray-600 text-lg">
                No predictions available. Run the pipeline to generate predictions.
              </p>
            </div>
          )}
        </div>

        {/* Info Section */}
        <div className="bg-blue-50 rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">About This Dashboard</h3>
          <ul className="text-blue-800 space-y-2">
            <li>
              ✅ <strong>Phase 1:</strong> Detects market events (earnings, acquisitions, etc.)
            </li>
            <li>
              ✅ <strong>Phase 2:</strong> Analyzes sentiment from news, Reddit, and StockTwits
            </li>
            <li>
              ✅ <strong>Phase 3:</strong> Uses trained ML models for predictions
            </li>
            <li>
              ✅ <strong>Phase 4:</strong> Real-time API with automated hourly updates
            </li>
            <li>
              ✅ <strong>Phase 5:</strong> Interactive web dashboard for visualizations
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};
