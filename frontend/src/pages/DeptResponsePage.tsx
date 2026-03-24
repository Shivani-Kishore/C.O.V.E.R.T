/**
 * C.O.V.E.R.T - Department Response Page
 * Clean page for departments to respond to routed reports.
 * No wallet connection needed — token-based auth.
 */

import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  BuildingOffice2Icon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { API_BASE } from '@/config';

const ORANGE = '#E84B1A';

interface DeptData {
  dept_name: string;
  report_id: string;
  current_status: string;
  current_response: string | null;
  routed_at: string | null;
  report_public_url: string;
}

const VALID_STATUSES = ['IN_PROGRESS', 'RESOLVED', 'NO_ACTION'] as const;
type ResponseStatus = (typeof VALID_STATUSES)[number];

export function DeptResponsePage() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<DeptData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [status, setStatus] = useState<ResponseStatus>('IN_PROGRESS');
  const [response, setResponse] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/routing/dept-response/${token}`);
        if (!res.ok) {
          setError(res.status === 404 ? 'This response link is invalid or has expired.' : 'Failed to load.');
          return;
        }
        const d = await res.json();
        setData(d);
        if (d.current_status && d.current_status !== 'PENDING') {
          setStatus(d.current_status as ResponseStatus);
        }
        if (d.current_response) {
          setResponse(d.current_response);
        }
      } catch {
        setError('Network error. Please try again.');
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  const handleSubmit = async () => {
    if (!token) return;
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/routing/dept-response/${token}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, response: response || undefined }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || 'Update failed');
      }
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-neutral-700 border-t-neutral-300 rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center px-4">
        <div className="max-w-md text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h1 className="text-xl font-bold text-white mb-2">Error</h1>
          <p className="text-neutral-400">{error || 'Something went wrong.'}</p>
        </div>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center px-4">
        <div className="max-w-md text-center">
          <CheckCircleIcon className="h-14 w-14 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-white mb-2">Response Recorded</h1>
          <p className="text-neutral-400 mb-6">
            The public report has been updated with your department's response.
          </p>
          <Link
            to={`/report/${data.report_id}`}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90"
            style={{ backgroundColor: ORANGE }}
          >
            View Public Report
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white px-4 py-12">
      <div className="max-w-lg mx-auto">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: 'rgba(232,75,26,0.14)' }}
          >
            <BuildingOffice2Icon className="h-5 w-5" style={{ color: ORANGE }} />
          </div>
          <div>
            <p className="text-xs text-neutral-500 uppercase tracking-wider">Department Response</p>
            <h1 className="text-lg font-bold text-white">
              You are responding as {data.dept_name}
            </h1>
          </div>
        </div>

        {/* Current info */}
        <div className="p-4 bg-neutral-900 border border-neutral-800 rounded-xl mb-6 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-neutral-500">Current Status</span>
            <span className="font-semibold text-white">{data.current_status}</span>
          </div>
          {data.current_response && (
            <div>
              <span className="text-xs text-neutral-500">Previous Response</span>
              <p className="text-sm text-neutral-300 italic mt-1">"{data.current_response}"</p>
            </div>
          )}
          <div className="flex justify-between text-sm">
            <span className="text-neutral-500">Routed</span>
            <span className="text-neutral-300">
              {data.routed_at ? new Date(data.routed_at).toLocaleDateString() : '—'}
            </span>
          </div>
        </div>

        {/* Form */}
        <div className="space-y-5">
          <div>
            <label className="block text-sm font-semibold text-neutral-300 mb-2">Status</label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as ResponseStatus)}
              className="w-full px-4 py-3 rounded-xl border border-neutral-700 bg-neutral-900 text-white text-sm focus:ring-2 focus:ring-neutral-500 focus:border-neutral-500"
            >
              <option value="IN_PROGRESS">In Progress</option>
              <option value="RESOLVED">Resolved</option>
              <option value="NO_ACTION">No Action</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-neutral-300 mb-2">
              Public response <span className="text-neutral-600 font-normal">(visible to citizens, optional)</span>
            </label>
            <textarea
              value={response}
              onChange={(e) => setResponse(e.target.value)}
              maxLength={500}
              rows={4}
              placeholder="Describe what action your department is taking..."
              className="w-full px-4 py-3 rounded-xl border border-neutral-700 bg-neutral-900 text-white text-sm placeholder-neutral-600 resize-none focus:ring-2 focus:ring-neutral-500 focus:border-neutral-500"
            />
            <p className="text-xs text-neutral-600 mt-1 text-right">{response.length}/500</p>
          </div>

          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full px-6 py-3.5 rounded-xl text-sm font-semibold text-white transition-all hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ backgroundColor: ORANGE }}
          >
            {submitting ? 'Submitting...' : 'Submit Response'}
          </button>
        </div>

        {/* Link to public report */}
        <div className="mt-8 text-center">
          <Link
            to={`/report/${data.report_id}`}
            className="text-sm text-neutral-500 hover:text-white transition-colors"
          >
            View public report →
          </Link>
        </div>
      </div>
    </div>
  );
}

export default DeptResponsePage;
