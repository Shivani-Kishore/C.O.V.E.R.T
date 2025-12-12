/**
 * C.O.V.E.R.T - Moderation Queue Component
 */

import { useEffect, useState } from 'react';
import {
  FunnelIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  ShieldExclamationIcon,
} from '@heroicons/react/24/outline';
import { useModerationStore, type QueueReport } from '@/stores/moderationStore';
import { ModerationModal } from './ModerationModal';

const CATEGORY_OPTIONS = [
  { value: '', label: 'All Categories' },
  { value: 'corruption', label: 'Corruption' },
  { value: 'fraud', label: 'Fraud' },
  { value: 'safety', label: 'Safety Violation' },
  { value: 'environment', label: 'Environmental' },
  { value: 'human_rights', label: 'Human Rights' },
  { value: 'other', label: 'Other' },
];

const RISK_OPTIONS = [
  { value: '', label: 'All Risk Levels' },
  { value: 'critical', label: 'Critical' },
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getRiskBadgeColor(risk?: string): string {
  switch (risk) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-200';
    case 'high':
      return 'bg-orange-100 text-orange-800 border-orange-200';
    case 'medium':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case 'low':
      return 'bg-green-100 text-green-800 border-green-200';
    default:
      return 'bg-neutral-100 text-neutral-800 border-neutral-200';
  }
}

export function ModerationQueue() {
  const { queue, filters, fetchQueue, setFilters, isLoadingQueue } = useModerationStore();
  const [selectedReport, setSelectedReport] = useState<QueueReport | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchQueue(filters);
  }, [filters, fetchQueue]);

  const handleRefresh = () => {
    fetchQueue(filters);
  };

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilters({ ...filters, category: e.target.value || undefined });
  };

  const handleRiskChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilters({ ...filters, risk_level: e.target.value || undefined });
  };

  const handleReviewComplete = () => {
    setSelectedReport(null);
    fetchQueue(filters);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Moderation Queue</h1>
          <p className="text-neutral-600 mt-1">
            {queue.length} report{queue.length !== 1 ? 's' : ''} pending review
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center px-4 py-2 border rounded-lg transition-colors ${
              showFilters
                ? 'border-primary-500 bg-primary-50 text-primary-600'
                : 'border-neutral-300 text-neutral-600 hover:bg-neutral-50'
            }`}
          >
            <FunnelIcon className="h-5 w-5 mr-2" />
            Filters
          </button>

          <button
            onClick={handleRefresh}
            disabled={isLoadingQueue}
            className="p-2 border border-neutral-300 rounded-lg text-neutral-600 hover:bg-neutral-50 transition-colors disabled:opacity-50"
          >
            <ArrowPathIcon className={`h-5 w-5 ${isLoadingQueue ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="bg-white rounded-lg border border-neutral-200 p-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Category
              </label>
              <select
                value={filters.category || ''}
                onChange={handleCategoryChange}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                {CATEGORY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">
                Risk Level
              </label>
              <select
                value={filters.risk_level || ''}
                onChange={handleRiskChange}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                {RISK_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Queue List */}
      {isLoadingQueue ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <p className="mt-2 text-neutral-600">Loading queue...</p>
        </div>
      ) : queue.length === 0 ? (
        <div className="bg-white rounded-lg border border-neutral-200 p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-neutral-100 rounded-full flex items-center justify-center">
            <ShieldExclamationIcon className="h-8 w-8 text-neutral-400" />
          </div>
          <h3 className="text-lg font-medium text-neutral-900 mb-2">
            No Reports in Queue
          </h3>
          <p className="text-neutral-600">
            There are no pending reports matching your filters.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {queue.map((report) => (
            <div
              key={report.id}
              onClick={() => setSelectedReport(report)}
              className="bg-white rounded-lg border border-neutral-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Risk and Category Badges */}
                  <div className="flex items-center space-x-2 mb-2">
                    {report.risk_level && (
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium border ${getRiskBadgeColor(
                          report.risk_level
                        )}`}
                      >
                        <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                        {report.risk_level.toUpperCase()}
                      </span>
                    )}
                    <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-neutral-100 text-neutral-700">
                      {report.category}
                    </span>
                  </div>

                  {/* Report Info */}
                  <p className="text-sm font-medium text-neutral-900 mb-1">
                    Report #{report.id.slice(0, 8)}
                  </p>
                  <p className="text-xs text-neutral-600">
                    Submitted {formatDate(report.submitted_at)} • {formatFileSize(report.size_bytes)}
                  </p>

                  {/* CID Preview */}
                  <p className="text-xs text-neutral-400 mt-2 font-mono">
                    CID: {report.cid.slice(0, 20)}...
                  </p>
                </div>

                {/* Credibility Score */}
                {report.verification_score !== undefined && (
                  <div className="ml-4 text-center">
                    <p className="text-xs text-neutral-600">Credibility</p>
                    <p
                      className={`text-xl font-bold ${
                        report.verification_score >= 0.7
                          ? 'text-green-600'
                          : report.verification_score >= 0.4
                            ? 'text-yellow-600'
                            : 'text-red-600'
                      }`}
                    >
                      {(report.verification_score * 100).toFixed(0)}%
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Moderation Modal */}
      {selectedReport && (
        <ModerationModal
          report={selectedReport}
          onClose={() => setSelectedReport(null)}
          onComplete={handleReviewComplete}
        />
      )}
    </div>
  );
}

export default ModerationQueue;
