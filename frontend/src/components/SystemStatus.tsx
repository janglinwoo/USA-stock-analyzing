import React, { useEffect, useState } from 'react';
import { SystemStatus, JobStatus } from '@types';
import { apiClient } from '@api/client';
import { Activity, Clock, Database, Zap } from 'lucide-react';

export const SystemStatusComponent: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [jobs, setJobs] = useState<JobStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const [statusData, jobsData] = await Promise.all([
          apiClient.getStatus(),
          apiClient.getScheduledJobs(),
        ]);
        setStatus(statusData);
        setJobs(jobsData);
        setError(null);
      } catch (err) {
        setError('Failed to load system status');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    loadStatus();
    const stopPolling = apiClient.startPolling(setStatus, 30000);

    return () => stopPolling();
  }, []);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
        <div className="h-4 bg-gray-200 rounded mb-4"></div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="bg-red-50 rounded-lg shadow-md p-6">
        <p className="text-red-800">{error || 'Failed to load status'}</p>
      </div>
    );
  }

  const uptime = Math.floor(status.uptime_seconds / 60); // Convert to minutes

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      {/* Status Card */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm font-medium">System Status</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {status.status === 'running' ? '✅ Running' : '⚠️ ' + status.status}
            </p>
          </div>
          <Activity
            className={`w-8 h-8 ${
              status.status === 'running' ? 'text-green-600' : 'text-yellow-600'
            }`}
          />
        </div>
      </div>

      {/* Uptime Card */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm font-medium">Uptime</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{uptime}m</p>
          </div>
          <Clock className="w-8 h-8 text-blue-600" />
        </div>
      </div>

      {/* Database Card */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm font-medium">Database</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {status.database_connected ? '✅ Connected' : '❌ Down'}
            </p>
          </div>
          <Database
            className={`w-8 h-8 ${
              status.database_connected ? 'text-green-600' : 'text-red-600'
            }`}
          />
        </div>
      </div>

      {/* Predictions Card */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm font-medium">Recent Predictions (24h)</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {status.recent_predictions_count}
            </p>
          </div>
          <Zap className="w-8 h-8 text-purple-600" />
        </div>
      </div>

      {/* Scheduled Jobs */}
      <div className="md:col-span-4 bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Scheduled Jobs ({jobs.length})</h3>
        {jobs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {jobs.map((job) => (
              <div
                key={job.job_id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-900">{job.job_name}</p>
                  <p className="text-sm text-gray-600">
                    {job.is_active ? '🟢 Active' : '🔴 Inactive'}
                  </p>
                  {job.next_run_time && (
                    <p className="text-xs text-gray-500 mt-1">
                      Next: {new Date(job.next_run_time).toLocaleTimeString()}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">No scheduled jobs</p>
        )}
      </div>
    </div>
  );
};
