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
  LockClosedIcon,
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import { ethers } from 'ethers';
import { useReportStore, type ReportStatus, type ReportCategory, type Report } from '@/stores/reportStore';
import { ReportCard } from './ReportCard';
import { mapApiReports } from '@/utils/reportMapper';
import { useWeb3 } from '@/hooks/useWeb3';
import { useReviewDecisionStore } from '@/stores/reviewDecisionStore';
import { useCovBalanceStore, STAKE_AMOUNTS, PARTIAL_RETURN_RATE, FINAL_SETTLEMENT_RATE, type VisibilityKey } from '@/stores/covBalanceStore';
import { protocolService } from '@/services/protocol';
import { STAKES } from '@/types/protocol';
import { API_BASE } from '@/config';

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

/**
 * Check freshly-loaded reports for stake return milestones and apply COV credits.
 *
 * Called after every report fetch (initial load + manual refresh).
 * Idempotent: each action is guarded by a persisted flag in reviewDecisionStore
 * so double-loading never double-credits the wallet.
 */
function applyStakeReturns(freshReports: Report[], walletAddress: string) {
  const covStore = useCovBalanceStore.getState();
  const decStore = useReviewDecisionStore.getState();
  const addr = walletAddress.toLowerCase();
  let repRefreshNeeded = false;

  for (const report of freshReports) {
    const stakeAmount = STAKE_AMOUNTS[report.visibility as VisibilityKey] ?? 0;

    // ── 25% partial return when status moves to under_review (reviewer passed) ──
    // Note: isMajorityPassed() only works in the reviewer's browser (they record
    // their own votes locally). For the reporter's wallet we rely solely on the
    // backend status being 'under_review', which is set when a reviewer passes.
    if (
      report.status === 'under_review' &&
      !decStore.isPartialReturnApplied(report.id, addr)
    ) {
      const partialReturn = Math.floor(stakeAmount * PARTIAL_RETURN_RATE);
      covStore.addBalance(addr, partialReturn);
      decStore.markPartialReturnApplied(report.id, addr);
      toast.success(`${partialReturn} COV returned — review majority passed!`, {
        id: `pr-${report.id}`,
      });
    }

    // ── 75% final settlement when moderator has finalized the report ──
    if (
      (report.status === 'verified' || report.status === 'rejected' || report.status === 'disputed') &&
      !decStore.isFinalSettlementApplied(report.id, addr)
    ) {
      // rejected = FALSE_OR_MANIPULATED → stake burned → 0 returned
      // verified / disputed → remaining 75% returned to reporter
      const finalReturn =
        report.status === 'rejected'
          ? 0
          : Math.floor(stakeAmount * FINAL_SETTLEMENT_RATE);

      if (finalReturn > 0) covStore.addBalance(addr, finalReturn);
      decStore.markFinalSettlementApplied(report.id, addr);
      repRefreshNeeded = true;

      const label =
        report.status === 'verified' ? 'Verified' :
        report.status === 'rejected' ? 'Rejected' : 'Disputed';
      const msg = finalReturn > 0
        ? `${label} — ${finalReturn} COV returned to your balance`
        : `${label} — stake slashed (false/manipulated report)`;
      toast(msg, { id: `fs-${report.id}`, duration: 5000 });
    }
  }

  // Trigger rep re-fetch in useRoleAccess so ProfileButton shows updated score
  if (repRefreshNeeded) {
    window.dispatchEvent(new CustomEvent('covert:rep-refresh'));
  }
}

export function MySubmissions() {
  const navigate = useNavigate();
  const { walletState, connect } = useWeb3();
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

  const isConnected = walletState.connected;

  const fetchReports = useCallback(async () => {
    if (!isConnected) {
      setReports([]);
      return;
    }
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const walletAddress = localStorage.getItem('wallet_address');
      const response = await fetch(`${API_BASE}/api/v1/reports`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          ...(walletAddress ? { 'X-Wallet-Address': walletAddress } : {}),
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch reports');
      }

      const data = await response.json();
      const freshReports = mapApiReports(data.items || []);

      // Enrich reports with on-chain data (reviewDecision, hasAppeal, etc.)
      if (import.meta.env.VITE_COVERT_PROTOCOL_ADDRESS) {
        try {
          await protocolService.connect();
          const enriched = await Promise.all(
            freshReports.map(async (r) => {
              if (!r.commitmentHash) return r;
              try {
                const onChainId = await protocolService.getReportIdByHash(r.commitmentHash);
                if (onChainId === null) return r;
                const onChain = await protocolService.getReport(onChainId);
                if (!onChain) return r;
                return {
                  ...r,
                  onChainId,
                  reviewDecision: onChain.reviewDecision,
                  hasAppeal: onChain.hasAppeal,
                  finalizedAt: onChain.finalizedAt,
                };
              } catch {
                return r;
              }
            })
          );
          setReports(enriched);
          if (walletAddress) applyStakeReturns(enriched, walletAddress);
        } catch {
          setReports(freshReports);
          if (walletAddress) applyStakeReturns(freshReports, walletAddress);
        }
      } else {
        setReports(freshReports);
        if (walletAddress) applyStakeReturns(freshReports, walletAddress);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reports');
      toast.error('Failed to load reports');
    } finally {
      setLoading(false);
    }
  }, [isConnected, setReports, setLoading, setError]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  // Re-fetch when a reviewer or moderator records a decision so statuses stay current
  useEffect(() => {
    window.addEventListener('covert:reports-updated', fetchReports);
    return () => window.removeEventListener('covert:reports-updated', fetchReports);
  }, [fetchReports]);

  // Poll for updates every 30s so cross-browser changes (e.g. moderator finalization) are picked up
  useEffect(() => {
    if (!isConnected) return;
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') fetchReports();
    }, 30_000);
    return () => clearInterval(interval);
  }, [isConnected, fetchReports]);

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

  const deleteReport = useCallback(async (id: string) => {
    const walletAddress = walletState.address || localStorage.getItem('wallet_address') || '';
    const response = await fetch(`${API_BASE}/api/v1/reports/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        ...(walletAddress ? { 'X-Wallet-Address': walletAddress } : {}),
      },
    });
    if (!response.ok) throw new Error(`Server returned ${response.status}`);
    removeReport(id);
  }, [walletState.address, removeReport]);

  const handleDeleteOne = useCallback(async (id: string) => {
    const confirmed = window.confirm('Delete this report? This action cannot be undone.');
    if (!confirmed) return;
    try {
      await deleteReport(id);
      toast.success('Report deleted');
    } catch {
      toast.error('Failed to delete report');
    }
  }, [deleteReport]);

  const handleDeleteSelected = useCallback(async () => {
    if (selectedReports.length === 0) return;

    const confirmed = window.confirm(
      `Delete ${selectedReports.length} selected report(s)? This action cannot be undone.`
    );
    if (!confirmed) return;

    let failed = 0;
    for (const id of selectedReports) {
      try {
        await deleteReport(id);
      } catch {
        failed++;
      }
    }

    setSelectedReports([]);
    if (failed === 0) {
      toast.success(`${selectedReports.length} report(s) deleted`);
    } else {
      toast.error(`${failed} deletion(s) failed`);
    }
  }, [selectedReports, deleteReport]);

  const handleRefresh = useCallback(async () => {
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      const walletAddress = localStorage.getItem('wallet_address');
      const response = await fetch(`${API_BASE}/api/v1/reports`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          ...(walletAddress ? { 'X-Wallet-Address': walletAddress } : {}),
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch reports');
      }

      const data = await response.json();
      const freshReports = mapApiReports(data.items || []);
      setReports(freshReports);
      if (walletAddress) applyStakeReturns(freshReports, walletAddress);
      toast.success('Reports refreshed');
    } catch (err) {
      toast.error('Failed to refresh reports');
    } finally {
      setLoading(false);
    }
  }, [setReports, setLoading]);

  const handleAppeal = useCallback(async (report: Report) => {
    if (report.onChainId === undefined) {
      toast.error('Report not found on-chain');
      return;
    }

    const confirmed = window.confirm(
      `Appeal this report? This will stake ${STAKES.APPEAL_BOND} COV as an appeal bond. ` +
      `If the appeal succeeds, your bond is returned. If not, it may be forfeited.`
    );
    if (!confirmed) return;

    try {
      await protocolService.connect();

      // Check COV balance
      const signerAddr = await protocolService.getSignerAddress();
      if (signerAddr) {
        const userState = await protocolService.getUserState(signerAddr);
        const covBalance = parseFloat(userState.covBalance);
        if (covBalance < STAKES.APPEAL_BOND) {
          toast.error(
            `Insufficient COV credits. You need ${STAKES.APPEAL_BOND} COV to appeal but your balance is ${covBalance.toFixed(2)} COV.`
          );
          return;
        }
      }

      const appealReasonHash = ethers.keccak256(
        ethers.toUtf8Bytes(`appeal:${report.commitmentHash}:${Date.now()}`)
      );

      toast.loading('Submitting appeal — confirm in your wallet...', { id: 'appeal' });
      await protocolService.appeal(report.onChainId, appealReasonHash);
      toast.success('Appeal submitted successfully!', { id: 'appeal' });

      // Sync updated balance
      if (signerAddr) {
        const updated = await protocolService.getUserState(signerAddr);
        useCovBalanceStore.getState().setBalance(signerAddr, parseFloat(updated.covBalance));
      }

      // Refresh reports to reflect the new appeal state
      fetchReports();
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Appeal failed';
      if (msg.includes('user rejected') || msg.includes('User denied')) {
        toast.dismiss('appeal');
        toast.error('Transaction rejected');
      } else if (msg.includes('0x43fb9453') || msg.toLowerCase().includes('insufficientcredits')) {
        toast.error('Insufficient COV credits for appeal.', { id: 'appeal' });
      } else if (msg.toLowerCase().includes('alreadyappealed')) {
        toast.error('This report has already been appealed.', { id: 'appeal' });
      } else {
        toast.error(`Appeal failed: ${msg}`, { id: 'appeal' });
      }
    }
  }, [fetchReports]);

  const filteredReports = getFilteredReports();

  const stats = {
    total: reports.length,
    pending: reports.filter((r) => r.status === 'pending').length,
    verified: reports.filter((r) => r.status === 'verified').length,
    rejected: reports.filter((r) => r.status === 'rejected').length,
  };

  if (!isConnected) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-white">My Submissions</h1>
          <p className="text-neutral-500 mt-1">Connect your wallet to view your reports</p>
        </div>
        <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-neutral-900 rounded-full flex items-center justify-center">
            <LockClosedIcon className="h-8 w-8 text-neutral-600" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">Wallet Not Connected</h3>
          <p className="text-neutral-500 mb-6">
            Please connect your wallet to see your submitted reports.
          </p>
          <button
            onClick={() => connect()}
            className="px-6 py-2.5 rounded-full font-medium transition-all duration-200 hover:opacity-90"
            style={{ backgroundColor: '#E84B1A', color: '#fff' }}
          >
            Connect Wallet
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">My Submissions</h1>
          <p className="text-neutral-500 mt-1">
            {stats.total} report{stats.total !== 1 ? 's' : ''} submitted
          </p>
        </div>
        <button
          onClick={() => navigate('/submit')}
          className="flex items-center px-5 py-2.5 rounded-full font-medium transition-all duration-200 hover:opacity-90"
          style={{ backgroundColor: '#E84B1A', color: '#fff' }}
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          New Report
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total', value: stats.total },
          { label: 'Pending', value: stats.pending },
          { label: 'Verified', value: stats.verified },
          { label: 'Rejected', value: stats.rejected },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
            <p className="text-sm text-neutral-500">{label}</p>
            <p className="text-2xl font-bold text-white">{value}</p>
          </div>
        ))}</div>

      {/* Search and Filters */}
      <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4">
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-neutral-600" />
            <input
              type="text"
              placeholder="Search by title or ID..."
              value={filters.search || ''}
              onChange={handleSearchChange}
              className="w-full pl-10 pr-4 py-2 border border-neutral-700 rounded-lg bg-neutral-900 text-white placeholder-neutral-600 focus:ring-2 focus:ring-neutral-600 focus:border-neutral-500"
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center px-4 py-2 border rounded-lg transition-colors ${showFilters ? 'border-neutral-500 bg-neutral-800 text-white' : 'border-neutral-700 text-neutral-400 hover:border-neutral-500 hover:text-white'
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
            className="p-2 border border-neutral-700 rounded-lg text-neutral-400 hover:text-white hover:border-neutral-500 transition-colors disabled:opacity-50"
          >
            <ArrowPathIcon className={`h-5 w-5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>

          {/* Delete Selected */}
          {selectedReports.length > 0 && (
            <button
              onClick={handleDeleteSelected}
              className="flex items-center px-4 py-2 rounded-lg font-medium transition-all hover:opacity-90"
              style={{ backgroundColor: '#E84B1A', color: '#fff' }}
            >
              <TrashIcon className="h-5 w-5 mr-2" />
              Delete ({selectedReports.length})
            </button>
          )}
        </div>

        {/* Expanded Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-neutral-800 grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-neutral-400 mb-1">Status</label>
              <select
                value={filters.status || ''}
                onChange={handleStatusChange}
                className="w-full px-3 py-2 border border-neutral-700 rounded-lg bg-neutral-900 text-neutral-300 focus:ring-2 focus:ring-neutral-600"
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-400 mb-1">Category</label>
              <select
                value={filters.category || ''}
                onChange={handleCategoryChange}
                className="w-full px-3 py-2 border border-neutral-700 rounded-lg bg-neutral-900 text-neutral-300 focus:ring-2 focus:ring-neutral-600"
              >
                {CATEGORY_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-neutral-400 mb-1">Sort By</label>
              <select
                value={`${filters.sortBy}-${filters.sortOrder}`}
                onChange={handleSortChange}
                className="w-full px-3 py-2 border border-neutral-700 rounded-lg bg-neutral-900 text-neutral-300 focus:ring-2 focus:ring-neutral-600"
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
                className="text-sm text-neutral-400 hover:text-white transition-colors"
              >
                Reset Filters
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Reports List */}
      {error ? (
        <div className="rounded-2xl border border-red-900/50 bg-red-950/20 p-6 text-center">
          <p className="text-red-400">{error}</p>
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
            <div key={i} className="rounded-2xl border border-neutral-800 bg-neutral-950 p-6 animate-pulse">
              <div className="flex items-center space-x-2 mb-4">
                <div className="h-6 w-20 bg-neutral-800 rounded-full" />
                <div className="h-6 w-24 bg-neutral-800 rounded-full" />
              </div>
              <div className="h-6 w-3/4 bg-neutral-800 rounded mb-2" />
              <div className="h-4 w-1/2 bg-neutral-800 rounded" />
            </div>
          ))}
        </div>
      ) : filteredReports.length === 0 ? (
        <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-12 text-center">
          <div className="w-16 h-16 mx-auto mb-4 bg-neutral-900 rounded-full flex items-center justify-center">
            <EyeIcon className="h-8 w-8 text-neutral-600" />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">No Reports Found</h3>
          <p className="text-neutral-500 mb-6">
            {reports.length === 0
              ? "You haven't submitted any reports yet."
              : 'No reports match your current filters.'}
          </p>
          {reports.length === 0 ? (
            <button
              onClick={() => navigate('/submit')}
              className="px-6 py-2.5 rounded-full font-medium transition-all duration-200 hover:opacity-90"
              style={{ backgroundColor: '#E84B1A', color: '#fff' }}
            >
              Submit Your First Report
            </button>
          ) : (
            <button
              onClick={resetFilters}
              className="px-6 py-2 bg-neutral-800 text-neutral-300 rounded-lg hover:bg-neutral-700 transition-colors"
            >
              Clear Filters
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredReports.map((report) => (
            <ReportCard
              key={report.id}
              report={report}
              onDelete={handleDeleteOne}
              onAppeal={
                report.onChainId !== undefined &&
                report.reviewDecision !== undefined &&
                report.reviewDecision !== 0 &&
                !report.hasAppeal &&
                (report.status === 'rejected' || report.status === 'disputed')
                  ? handleAppeal
                  : undefined
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default MySubmissions;
