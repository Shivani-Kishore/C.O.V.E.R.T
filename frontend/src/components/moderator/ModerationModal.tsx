/**
 * C.O.V.E.R.T - Moderation Modal Component
 */

import { useState, useEffect } from 'react';
import {
  XMarkIcon,
  CheckIcon,
  XCircleIcon,
  InformationCircleIcon,
  ArrowUpIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { useModerationStore, type QueueReport, type ModerationDecision } from '@/stores/moderationStore';

interface ModerationModalProps {
  report: QueueReport;
  onClose: () => void;
  onComplete: () => void;
}

const DECISION_OPTIONS: { value: ModerationDecision; label: string; icon: React.ElementType; color: string }[] = [
  {
    value: 'accept',
    label: 'Accept Report',
    icon: CheckIcon,
    color: 'bg-green-600 hover:bg-green-700',
  },
  {
    value: 'reject',
    label: 'Reject Report',
    icon: XCircleIcon,
    color: 'bg-red-600 hover:bg-red-700',
  },
  {
    value: 'need_info',
    label: 'Request More Info',
    icon: InformationCircleIcon,
    color: 'bg-yellow-600 hover:bg-yellow-700',
  },
  {
    value: 'escalate',
    label: 'Escalate to Senior',
    icon: ArrowUpIcon,
    color: 'bg-blue-600 hover:bg-blue-700',
  },
];

export function ModerationModal({ report, onClose, onComplete }: ModerationModalProps) {
  const { startReview, stopReview, updateNotes, getReviewDuration, currentReview } = useModerationStore();
  const [decision, setDecision] = useState<ModerationDecision | null>(null);
  const [notes, setNotes] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reviewTime, setReviewTime] = useState(0);

  useEffect(() => {
    // Start review timer
    startReview(report.id);

    // Update timer every second
    const interval = setInterval(() => {
      setReviewTime(getReviewDuration());
    }, 1000);

    return () => {
      clearInterval(interval);
      stopReview();
    };
  }, [report.id, startReview, stopReview, getReviewDuration]);

  const handleNotesChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setNotes(e.target.value);
    updateNotes(e.target.value);
  };

  const handleSubmit = async () => {
    if (!decision) {
      toast.error('Please select a decision');
      return;
    }

    if (decision === 'reject' && !rejectionReason) {
      toast.error('Please provide a rejection reason');
      return;
    }

    setIsSubmitting(true);

    try {
      // Start review (marks as under_review)
      const moderatorId = localStorage.getItem('moderator_id');
      const startResponse = await fetch('/api/v1/moderation/review/start', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Moderator-ID': moderatorId || '',
        },
        body: JSON.stringify({
          report_id: report.id,
        }),
      });

      if (!startResponse.ok) {
        throw new Error('Failed to start review');
      }

      // Submit decision
      const response = await fetch('/api/v1/moderation/review/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Moderator-ID': moderatorId || '',
        },
        body: JSON.stringify({
          report_id: report.id,
          decision,
          encrypted_notes: notes || null,
          rejection_reason: decision === 'reject' ? rejectionReason : null,
          time_spent_seconds: reviewTime,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit decision');
      }

      toast.success(`Report ${decision}ed successfully`);
      onComplete();
    } catch (error) {
      console.error('Submission error:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to submit decision');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />

      {/* Modal */}
      <div className="relative min-h-screen flex items-center justify-center p-4">
        <div className="relative bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-neutral-200">
            <div className="flex-1">
              <h2 className="text-xl font-bold text-neutral-900">
                Review Report #{report.id.slice(0, 8)}
              </h2>
              <p className="text-sm text-neutral-600 mt-1">
                Category: {report.category} • Submitted: {new Date(report.submitted_at).toLocaleString()}
              </p>
            </div>

            {/* Timer */}
            <div className="flex items-center mr-4 text-sm text-neutral-600">
              <ClockIcon className="h-4 w-4 mr-1" />
              {formatTime(reviewTime)}
            </div>

            <button
              onClick={onClose}
              className="p-2 hover:bg-neutral-100 rounded-lg transition-colors"
            >
              <XMarkIcon className="h-5 w-5 text-neutral-600" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {/* Report Metadata */}
            <div className="bg-neutral-50 rounded-lg p-4">
              <h3 className="font-medium text-neutral-900 mb-3">Report Metadata</h3>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-neutral-600">IPFS CID</p>
                  <p className="font-mono text-xs text-neutral-900 break-all">{report.cid}</p>
                </div>
                <div>
                  <p className="text-neutral-600">File Size</p>
                  <p className="text-neutral-900">
                    {(report.size_bytes / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
                {report.risk_level && (
                  <div>
                    <p className="text-neutral-600">Risk Level</p>
                    <p className="text-neutral-900 capitalize">{report.risk_level}</p>
                  </div>
                )}
                {report.verification_score !== undefined && (
                  <div>
                    <p className="text-neutral-600">AI Credibility Score</p>
                    <p className="text-neutral-900">
                      {(report.verification_score * 100).toFixed(1)}%
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Security Notice */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start">
                <InformationCircleIcon className="h-5 w-5 text-blue-500 mt-0.5 mr-3" />
                <div className="text-sm text-blue-700">
                  <p className="font-medium">Privacy Protected</p>
                  <p className="mt-1">
                    The actual report content is encrypted and not visible to moderators.
                    You are reviewing metadata only. Base your decision on file size, submission
                    patterns, AI credibility scores, and category appropriateness.
                  </p>
                </div>
              </div>
            </div>

            {/* Moderator Notes */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Moderator Notes (Optional)
              </label>
              <textarea
                value={notes}
                onChange={handleNotesChange}
                placeholder="Add private notes about this review..."
                rows={4}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg resize-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-xs text-neutral-500 mt-1">
                These notes are encrypted and only visible to you
              </p>
            </div>

            {/* Decision Selection */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-3">
                Decision <span className="text-red-500">*</span>
              </label>
              <div className="grid grid-cols-2 gap-3">
                {DECISION_OPTIONS.map((option) => {
                  const Icon = option.icon;
                  return (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setDecision(option.value)}
                      className={`p-4 border-2 rounded-lg transition-all text-left ${
                        decision === option.value
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-neutral-200 hover:border-neutral-300'
                      }`}
                    >
                      <div className="flex items-center">
                        <Icon className={`h-5 w-5 mr-2 ${
                          decision === option.value ? 'text-primary-600' : 'text-neutral-600'
                        }`} />
                        <span className={`font-medium ${
                          decision === option.value ? 'text-primary-900' : 'text-neutral-900'
                        }`}>
                          {option.label}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Rejection Reason (if reject selected) */}
            {decision === 'reject' && (
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-2">
                  Rejection Reason <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={rejectionReason}
                  onChange={(e) => setRejectionReason(e.target.value)}
                  placeholder="Explain why this report is being rejected..."
                  rows={3}
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg resize-none focus:ring-2 focus:ring-primary-500"
                />
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 p-6 border-t border-neutral-200">
            <button
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 border border-neutral-300 rounded-lg text-neutral-700 hover:bg-neutral-50 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={!decision || isSubmitting || (decision === 'reject' && !rejectionReason)}
              className={`px-6 py-2 rounded-lg text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                decision
                  ? DECISION_OPTIONS.find((o) => o.value === decision)?.color || 'bg-primary-600'
                  : 'bg-neutral-400'
              }`}
            >
              {isSubmitting ? 'Submitting...' : 'Submit Decision'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ModerationModal;
