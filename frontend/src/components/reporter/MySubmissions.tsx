/**
 * C.O.V.E.R.T - My Submissions Component
 */

import { useState, useEffect, useCallback } from 'react';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  PlusIcon,
  TrashIcon,
  EyeIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { useReportStore, type ReportStatus, type ReportCategory } from '@/stores/reportStore';
import { ReportCard } from './ReportCard';

const STATUS_OPTIONS: { value: ReportStatus | ''; label: string }[] = [
  { value: '', label: 'All Status' },
  { value: 'pending', label: 'Pending' },
  { value: 'under_review', label: 'Under Review' },
  { value: 'verified', label: 'Verified' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'disputed', label: 'Disputed' },
];

const CATEGORY_OPTIONS: { value: ReportCategory | ''; label: string }[] = [
  { value: '', label: 'All Categories' },
  { value: 'corruption', label: 'Corruption' },
  { value: 'fraud', label: 'Fraud' },
  { value: 'safety', label: 'Safety Violation' },
  { value: 'environment', label: 'Environmental' },
  { value: 'human_rights', label: 'Human Rights' },
  { value: 'other', label: 'Other' },
];

export function MySubmissions() {
  const navigate = useNavigate();
  const [showFilters, setShowFilters] = useState(false);
  const [selectedReports, setSelectedReports] = useState<string[]>([]);

  const {
    reports,
    isLoading,
    error,
    filters,
    setFilters,
    resetFilters,
    setReports,
    setLoading,
    setError,
    removeReport,
    getFilteredReports,
  } = useReportStore();

  // Fetch reports on mount
  useEffect(() => {
    const fetchReports = async () => {
      setLoading(true);
      setError(null);

      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/v1/reports', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch reports');
        }

        const data = await response.json();
        setReports(data.items || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load reports');
        toast.error('Failed to load reports');
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, [setReports, setLoading, setError]);

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setFilters({ search: e.target.value });
  }, [setFilters]);

  const handleStatusChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilters({ status: e.target.value as ReportStatus | undefined || undefined });
  }, [setFilters]);

  const handleCategoryChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    setFilters({ category: e.target.value as ReportCategory | undefined || undefined });
  }, [setFilters]);

  const handleSortChange = useCallback((e: React.ChangeEvent<HTMLSelectElement>) => {
    const [sortBy, sortOrder] = e.target.value.split('-') as [typeof filters.sortBy, typeof filters.sortOrder];
    setFilters({ sortBy, sortOrder });
  }, [setFilters]);

  const handleDeleteSelected = useCallback(async () => {
    if (selectedReports.length === 0) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedReports.length} report(s)?`
    );

    if (!confirmed) return;

    try {
      for (const id of selectedReports) {
        const response = await fetch(`/api/v1/reports/${id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
          },
        });

        if (response.ok) {
          removeReport(id);
        }
      }

      setSelectedReports([]);
      toast.success('Reports deleted successfully');
    } catch (err) {
      toast.error('Failed to delete some reports');
    }
  }, [selectedReports, removeReport]);

  const handleRefresh = useCallback(async () => {
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/reports', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch reports');
      }

      const data = await response.json();
      setReports(data.items || []);
      toast.success('Reports refreshed');
    } catch (err) {
      toast.error('Failed to refresh reports');
    } finally {
      setLoading(false);
    }
  }, [setReports, setLoading]);

  const filteredReports = getFilteredReports();

  // Stats
  const stats = {
    total: reports.length,
    pending: reports.filter((r) => r.status === 'pending').length,
    verified: reports.filter((r) => r.status === 'verified').length,
    rejected: reports.filter((r) => r.status === 'rejected').length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">My Submissions</h1>
          <p className="text-neutral-600 mt-1">
            {stats.total} report{stats.total !== 1 ? 's' : ''} submitted
          </p>
        </div>
        <button
          onClick={() => navigate('/submit')}
          className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          New Report
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-neutral-200 p-4">
          <p className="text-sm text-neutral-500">Total</p>
          <p className="text-2xl font-bold text-neutral-900">{stats.total}</p>
        </div>
        <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-4">
          <p className="text-sm text-yellow-700">Pending</p>
          <p className="text-2xl font-bold text-yellow-800">{stats.pending}</p>
        </div>
        <div className="bg-green-50 rounded-lg border border-green-200 p-4">
          <p className="text-sm text-green-700">Verified</p>
          <p className="text-2xl font-bold text-green-800">{stats.verified}</p>
        </div>
        <div className="bg-red-50 rounded-lg border border-red-200 p-4">
          <p className="text-sm text-red-700">Rejected</p>
          <p className="text-2xl font-bold text-red-800">{stats.rejected}</p>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg border border-neutral-200 p-4">
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-neutral-400" />
            <input
              type="text"
              placeholder="Search by title or ID..."
              value={filters.search || ''}
              onChange={handleSearchChange}
              className="w-full pl-10 pr-4 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center px-4 py-2 border rounded-lg transition-colors ${
              showFilters ? 'border-primary-500 bg-primary-50 text-primary-600' : 'border-neutral-300 text-neutral-600 hover:bg-neutral-50'
            }`}
          >
            <FunnelIcon className="h-5 w-5 mr-2" />
            Filters
            <ChevronDownIcon className={`h-4 w-4 ml-2 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>

          {/* Refresh */}
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="p-2 border border-neutral-300 rounded-lg text-neutral-600 hover:bg-neutral-50 transition-colors disabled:opacity-50"
          >
            <ArrowPathIcon className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>

          {/* Delete Selected */}
          {selectedReports.length > 0 && (
            <button
              onClick={handleDeleteSelected}
              className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              <TrashIcon className="h-5 w-5 mr-2" />
              Delete ({selectedReports.length})
            </button>
          )}
        </div>

        {/* Expanded Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-neutral-200 grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">Status</label>
              <select
                value={filters.status || ''}
                onChange={handleStatusChange}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">Category</label>
              <select
                value={filters.category || ''}
                onChange={handleCategoryChange}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                {CATEGORY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-1">Sort By</label>
              <select
                value={`${filters.sortBy}-${filters.sortOrder}`}
                onChange={handleSortChange}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="submittedAt-desc">Newest First</option>
                <option value="submittedAt-asc">Oldest First</option>
                <option value="status-asc">Status (A-Z)</option>
                <option value="category-asc">Category (A-Z)</option>
              </select>
            </div>

            <div className="col-span-3 flex justify-end">
              <button
                onClick={resetFilters}
                className="text-sm text-primary-600 hover:text-primary-700"
              >
                Reset Filters
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Reports List */}
      {error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-600">{error}</p>
          <button
            onClick={handleRefresh}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      ) : isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-lg border border-neutral-200 p-6 animate-pulse">
              <div className="flex items-center space-x-2 mb-4">
                <div className="h-6 w-20 bg-neutral-200 rounded-full" />
                <div className="h-6 w-24 bg-neutral-200 rounded-full" />
              </div>
              <div className="h-6 w-3/4 bg-neutral-200 rounded mb-2" />
              <div className="h-4 w-1/2 bg-neutral-200 rounded" />
            </div>
          ))}
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="bg-white rounded-lg border border-neutral-200 p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-neutral-100 rounded-full flex items-center justify-center">
            <EyeIcon className="h-8 w-8 text-neutral-400" />
          </div>
          <h3 className="text-lg font-medium text-neutral-900 mb-2">No Reports Found</h3>
          <p className="text-neutral-600 mb-6">
            {reports.length === 0
              ? "You haven't submitted any reports yet."
              : 'No reports match your current filters.'}
          </p>
          {reports.length === 0 ? (
            <button
              onClick={() => navigate('/submit')}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              Submit Your First Report
            </button>
          ) : (
            <button
              onClick={resetFilters}
              className="px-6 py-2 bg-neutral-200 text-neutral-700 rounded-lg hover:bg-neutral-300"
            >
              Clear Filters
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredReports.map((report) => (
            <ReportCard key={report.id} report={report} />
          ))}
        </div>
      )}
    </div>
  );
}

export default MySubmissions;
