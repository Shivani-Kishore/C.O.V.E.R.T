/**
 * C.O.V.E.R.T - Moderator Dashboard Page
 */

import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ClipboardDocumentCheckIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useModerationStore } from '@/stores/moderationStore';

export function ModeratorDashboard() {
  const { stats, queueSummary, fetchStats, fetchQueueSummary, isLoadingStats } = useModerationStore();

  useEffect(() => {
    fetchStats(30);
    fetchQueueSummary();
  }, [fetchStats, fetchQueueSummary]);

  const tierColors = {
    bronze: 'bg-orange-100 text-orange-800',
    silver: 'bg-gray-100 text-gray-800',
    gold: 'bg-yellow-100 text-yellow-800',
    platinum: 'bg-purple-100 text-purple-800',
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-xl p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">Moderator Dashboard</h1>
        <p className="text-primary-100">
          Review reports and maintain platform integrity
        </p>
      </div>

      {/* Moderator Stats */}
      {stats && (
        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-neutral-900">Your Performance</h2>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${tierColors[stats.tier]}`}>
              {stats.tier.charAt(0).toUpperCase() + stats.tier.slice(1)} Tier
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="p-4 bg-neutral-50 rounded-lg">
              <p className="text-sm text-neutral-600">Reputation Score</p>
              <p className="text-3xl font-bold text-neutral-900">{stats.reputation_score}</p>
            </div>

            <div className="p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-green-700">Accuracy Rate</p>
              <p className="text-3xl font-bold text-green-800">
                {(stats.accuracy_rate * 100).toFixed(1)}%
              </p>
            </div>

            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-700">Total Reviews</p>
              <p className="text-3xl font-bold text-blue-800">{stats.total_reviews}</p>
            </div>

            <div className="p-4 bg-neutral-50 rounded-lg">
              <p className="text-sm text-neutral-600">Avg Review Time</p>
              <p className="text-3xl font-bold text-neutral-900">
                {Math.floor(stats.average_review_time_seconds / 60)}m
              </p>
            </div>
          </div>

          {/* Recent Activity (Last 30 days) */}
          <div className="border-t border-neutral-200 pt-6">
            <h3 className="text-sm font-medium text-neutral-700 mb-4">
              Last 30 Days Activity
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-full mr-3">
                  <CheckCircleIcon className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-xs text-neutral-600">Accepted</p>
                  <p className="text-lg font-semibold text-neutral-900">
                    {stats.decisions.accept || 0}
                  </p>
                </div>
              </div>

              <div className="flex items-center">
                <div className="p-2 bg-red-100 rounded-full mr-3">
                  <XCircleIcon className="h-5 w-5 text-red-600" />
                </div>
                <div>
                  <p className="text-xs text-neutral-600">Rejected</p>
                  <p className="text-lg font-semibold text-neutral-900">
                    {stats.decisions.reject || 0}
                  </p>
                </div>
              </div>

              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-full mr-3">
                  <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600" />
                </div>
                <div>
                  <p className="text-xs text-neutral-600">Need Info</p>
                  <p className="text-lg font-semibold text-neutral-900">
                    {stats.decisions.need_info || 0}
                  </p>
                </div>
              </div>

              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-full mr-3">
                  <ChartBarIcon className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-xs text-neutral-600">Escalated</p>
                  <p className="text-lg font-semibold text-neutral-900">
                    {stats.decisions.escalate || 0}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Queue Summary */}
      {queueSummary && (
        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-neutral-900">Moderation Queue</h2>
            <Link
              to="/moderation/queue"
              className="text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              View Queue
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-yellow-700">Pending Reports</p>
                  <p className="text-3xl font-bold text-yellow-800">
                    {queueSummary.total_pending}
                  </p>
                </div>
                <ClipboardDocumentCheckIcon className="h-8 w-8 text-yellow-600" />
              </div>
            </div>

            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-700">Avg Wait Time</p>
                  <p className="text-3xl font-bold text-blue-800">
                    {queueSummary.average_wait_time_hours.toFixed(1)}h
                  </p>
                </div>
                <ClockIcon className="h-8 w-8 text-blue-600" />
              </div>
            </div>

            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-red-700">Oldest Report</p>
                  <p className="text-3xl font-bold text-red-800">
                    {queueSummary.oldest_report_age_hours.toFixed(1)}h
                  </p>
                </div>
                <ExclamationTriangleIcon className="h-8 w-8 text-red-600" />
              </div>
            </div>
          </div>

          {/* Risk Level Breakdown */}
          <div className="border-t border-neutral-200 pt-6">
            <h3 className="text-sm font-medium text-neutral-700 mb-4">
              Reports by Risk Level
            </h3>
            <div className="grid grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">
                  {queueSummary.by_risk_level.critical || 0}
                </p>
                <p className="text-xs text-neutral-600">Critical</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-600">
                  {queueSummary.by_risk_level.high || 0}
                </p>
                <p className="text-xs text-neutral-600">High</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-600">
                  {queueSummary.by_risk_level.medium || 0}
                </p>
                <p className="text-xs text-neutral-600">Medium</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {queueSummary.by_risk_level.low || 0}
                </p>
                <p className="text-xs text-neutral-600">Low</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/moderation/queue"
          className="p-6 bg-white border border-neutral-200 rounded-lg hover:shadow-md transition-shadow"
        >
          <ClipboardDocumentCheckIcon className="h-8 w-8 text-primary-600 mb-3" />
          <h3 className="font-semibold text-neutral-900 mb-1">Review Queue</h3>
          <p className="text-sm text-neutral-600">
            Start reviewing pending reports
          </p>
        </Link>

        <Link
          to="/moderation/history"
          className="p-6 bg-white border border-neutral-200 rounded-lg hover:shadow-md transition-shadow"
        >
          <ChartBarIcon className="h-8 w-8 text-primary-600 mb-3" />
          <h3 className="font-semibold text-neutral-900 mb-1">Review History</h3>
          <p className="text-sm text-neutral-600">
            View your moderation history
          </p>
        </Link>

        <Link
          to="/moderation/stats"
          className="p-6 bg-white border border-neutral-200 rounded-lg hover:shadow-md transition-shadow"
        >
          <ChartBarIcon className="h-8 w-8 text-primary-600 mb-3" />
          <h3 className="font-semibold text-neutral-900 mb-1">Detailed Stats</h3>
          <p className="text-sm text-neutral-600">
            View comprehensive statistics
          </p>
        </Link>
      </div>

      {/* Loading State */}
      {isLoadingStats && (
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-neutral-600">Loading dashboard...</p>
        </div>
      )}
    </div>
  );
}

export default ModeratorDashboard;
