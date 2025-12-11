/**
 * C.O.V.E.R.T - Report Card Component
 */

import { memo, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheckIcon,
  ChevronRightIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  EyeSlashIcon,
} from '@heroicons/react/24/outline';
import type { Report, ReportStatus, ReportVisibility, ReportCategory } from '@/stores/reportStore';

interface ReportCardProps {
  report: Report;
  onClick?: () => void;
  compact?: boolean;
}

const statusConfig: Record<ReportStatus, { label: string; color: string; icon: React.ElementType }> = {
  pending: {
    label: 'Pending',
    color: 'bg-yellow-100 text-yellow-800',
    icon: ClockIcon,
  },
  under_review: {
    label: 'Under Review',
    color: 'bg-blue-100 text-blue-800',
    icon: EyeIcon,
  },
  verified: {
    label: 'Verified',
    color: 'bg-green-100 text-green-800',
    icon: CheckCircleIcon,
  },
  rejected: {
    label: 'Rejected',
    color: 'bg-red-100 text-red-800',
    icon: XCircleIcon,
  },
  disputed: {
    label: 'Disputed',
    color: 'bg-orange-100 text-orange-800',
    icon: ExclamationTriangleIcon,
  },
};

const categoryLabels: Record<ReportCategory, string> = {
  corruption: 'Corruption',
  fraud: 'Fraud',
  safety: 'Safety Violation',
  environment: 'Environmental',
  human_rights: 'Human Rights',
  other: 'Other',
};

const visibilityConfig: Record<ReportVisibility, { label: string; icon: React.ElementType }> = {
  private: { label: 'Private', icon: EyeSlashIcon },
  moderated: { label: 'Moderated', icon: EyeIcon },
  public: { label: 'Public', icon: EyeIcon },
};

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function truncateHash(hash: string, length: number = 8): string {
  if (hash.length <= length * 2 + 3) return hash;
  return `${hash.slice(0, length)}...${hash.slice(-length)}`;
}

export const ReportCard = memo(function ReportCard({
  report,
  onClick,
  compact = false,
}: ReportCardProps) {
  const navigate = useNavigate();

  const formattedDate = useMemo(
    () => formatDate(report.submittedAt),
    [report.submittedAt]
  );

  const handleClick = useCallback(() => {
    if (onClick) {
      onClick();
    } else {
      navigate(`/report/${report.id}`);
    }
  }, [onClick, navigate, report.id]);

  const statusInfo = statusConfig[report.status];
  const StatusIcon = statusInfo.icon;
  const VisibilityIcon = visibilityConfig[report.visibility].icon;

  if (compact) {
    return (
      <div
        onClick={handleClick}
        className="flex items-center justify-between p-4 bg-white border border-neutral-200 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
      >
        <div className="flex items-center space-x-4">
          <div className={`flex items-center px-2 py-1 rounded-full text-xs font-medium ${statusInfo.color}`}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {statusInfo.label}
          </div>
          <span className="text-sm text-neutral-600">
            {categoryLabels[report.category]}
          </span>
          <span className="text-sm text-neutral-400">
            {formattedDate}
          </span>
        </div>
        <ChevronRightIcon className="h-5 w-5 text-neutral-400" />
      </div>
    );
  }

  return (
    <div
      onClick={handleClick}
      className="bg-white rounded-lg border border-neutral-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer p-6"
    >
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          {/* Status and Category Badges */}
          <div className="flex items-center space-x-2 mb-2">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.color}`}>
              <StatusIcon className="h-3 w-3 mr-1" />
              {statusInfo.label}
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-neutral-100 text-neutral-700">
              {categoryLabels[report.category]}
            </span>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-neutral-50 text-neutral-600">
              <VisibilityIcon className="h-3 w-3 mr-1" />
              {visibilityConfig[report.visibility].label}
            </span>
          </div>

          {/* Report ID/Title */}
          <h3 className="text-lg font-semibold text-neutral-900 mb-1">
            {report.title || `Report #${report.id.slice(0, 8)}`}
          </h3>

          {/* Submission Info */}
          <p className="text-sm text-neutral-600">
            Submitted {formattedDate} &bull; {formatFileSize(report.fileSize)}
          </p>
        </div>

        {/* Verification Score */}
        {report.verificationScore !== undefined && (
          <div className="flex flex-col items-end ml-4">
            <span className="text-sm text-neutral-600">Credibility</span>
            <span className={`text-2xl font-bold ${
              report.verificationScore >= 0.7
                ? 'text-green-600'
                : report.verificationScore >= 0.4
                  ? 'text-yellow-600'
                  : 'text-red-600'
            }`}>
              {(report.verificationScore * 100).toFixed(0)}%
            </span>
          </div>
        )}
      </div>

      {/* Transaction Info */}
      <div className="flex items-center justify-between pt-4 border-t border-neutral-200">
        <div className="flex items-center text-sm text-neutral-600">
          <ShieldCheckIcon className="h-4 w-4 mr-1 text-green-500" />
          <span>On-chain verified</span>
          <span className="mx-2">&bull;</span>
          <span className="font-mono text-xs">
            {truncateHash(report.commitmentHash)}
          </span>
        </div>

        <ChevronRightIcon className="h-5 w-5 text-neutral-400" />
      </div>

      {/* Risk Level Badge */}
      {report.riskLevel && (
        <div className="mt-3">
          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
            report.riskLevel === 'critical' ? 'bg-red-100 text-red-800' :
            report.riskLevel === 'high' ? 'bg-orange-100 text-orange-800' :
            report.riskLevel === 'medium' ? 'bg-yellow-100 text-yellow-800' :
            'bg-green-100 text-green-800'
          }`}>
            <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
            {report.riskLevel.charAt(0).toUpperCase() + report.riskLevel.slice(1)} Risk
          </span>
        </div>
      )}
    </div>
  );
});

export default ReportCard;
