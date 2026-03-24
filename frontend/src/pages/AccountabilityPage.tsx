/**
 * C.O.V.E.R.T - Accountability Dashboard
 * Public page showing department response rates and routing statistics.
 */

import { useEffect, useState } from 'react';
import {
  BuildingOffice2Icon,
  ChartBarIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';
import { API_BASE } from '@/config';

const ORANGE = '#E84B1A';

interface DeptStat {
  dept_name: string;
  short_name: string;
  total_routed: number;
  total_responded: number;
  total_resolved: number;
  response_rate_percent: number;
  avg_response_days: number | null;
  last_responded_at: string | null;
}

interface StatsData {
  summary: {
    total_reports_routed: number;
    overall_response_rate_percent: number;
    fastest_dept: string | null;
    slowest_dept: string | null;
  };
  departments: DeptStat[];
}

function rateColor(rate: number): string {
  if (rate >= 60) return '#22c55e'; // green
  if (rate >= 30) return '#f59e0b'; // amber
  return '#ef4444'; // red
}

export function AccountabilityPage() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/routing/stats`);
        if (res.ok) setStats(await res.json());
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="py-16 text-center text-neutral-500">Loading accountability data...</div>
    );
  }

  if (!stats) {
    return (
      <div className="py-16 text-center text-neutral-500">Failed to load data.</div>
    );
  }

  const { summary, departments } = stats;
  const activeDepts = departments.filter((d) => d.total_routed > 0);
  const inactiveDepts = departments.filter((d) => d.total_routed === 0);

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <h1 className="text-3xl font-bold text-white">Department Accountability</h1>
        <p className="text-neutral-400 mt-2">
          Track how Bangalore civic departments respond to citizen reports.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-10">
        <div className="p-6 bg-neutral-950 border border-neutral-800 rounded-2xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(232,75,26,0.12)' }}>
              <ChartBarIcon className="h-5 w-5" style={{ color: ORANGE }} />
            </div>
            <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider">Reports Routed</p>
          </div>
          <p className="text-3xl font-bold text-white">{summary.total_reports_routed}</p>
        </div>

        <div className="p-6 bg-neutral-950 border border-neutral-800 rounded-2xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(34,197,94,0.12)' }}>
              <BuildingOffice2Icon className="h-5 w-5 text-green-500" />
            </div>
            <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider">Response Rate</p>
          </div>
          <p className="text-3xl font-bold text-white">{summary.overall_response_rate_percent}%</p>
        </div>

        <div className="p-6 bg-neutral-950 border border-neutral-800 rounded-2xl">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'rgba(59,130,246,0.12)' }}>
              <ClockIcon className="h-5 w-5 text-blue-500" />
            </div>
            <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider">Fastest Department</p>
          </div>
          <p className="text-xl font-bold text-white">{summary.fastest_dept || '—'}</p>
        </div>
      </div>

      {/* Department Table */}
      <div className="bg-neutral-950 border border-neutral-800 rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-neutral-800">
          <h2 className="text-lg font-semibold text-white">All Departments</h2>
        </div>

        <div className="divide-y divide-neutral-800">
          {activeDepts.map((dept) => (
            <div key={dept.short_name} className="px-6 py-5">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="text-sm font-semibold text-white">{dept.dept_name}</p>
                  <p className="text-xs text-neutral-600 mt-0.5">{dept.short_name}</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-bold" style={{ color: rateColor(dept.response_rate_percent) }}>
                    {dept.response_rate_percent}%
                  </p>
                  <p className="text-xs text-neutral-600">{dept.total_routed} routed</p>
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full h-2 bg-neutral-800 rounded-full overflow-hidden mb-2">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${dept.response_rate_percent}%`,
                    backgroundColor: rateColor(dept.response_rate_percent),
                  }}
                />
              </div>

              <div className="flex items-center justify-between text-xs text-neutral-600">
                <span>
                  Avg response:{' '}
                  {dept.avg_response_days !== null
                    ? `${dept.avg_response_days} days`
                    : 'No responses yet'}
                </span>
                <span>
                  Last responded:{' '}
                  {dept.last_responded_at
                    ? new Date(dept.last_responded_at).toLocaleDateString()
                    : 'Never'}
                </span>
              </div>
            </div>
          ))}

          {/* Inactive departments greyed out */}
          {inactiveDepts.map((dept) => (
            <div key={dept.short_name} className="px-6 py-4 opacity-40">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-neutral-500">{dept.dept_name}</p>
                  <p className="text-xs text-neutral-700">{dept.short_name}</p>
                </div>
                <p className="text-xs text-neutral-700">No reports routed</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AccountabilityPage;
