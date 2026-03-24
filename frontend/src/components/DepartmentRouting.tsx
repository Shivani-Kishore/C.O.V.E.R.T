/**
 * C.O.V.E.R.T - Department Routing Section
 * Shows which departments have been notified about a report and their response status.
 */

import { useEffect, useState } from 'react';
import { BuildingOffice2Icon } from '@heroicons/react/24/outline';
import { API_BASE } from '@/config';

interface RoutingEntry {
  dept_name: string;
  short_name: string;
  status: string;
  department_response: string | null;
  responded_at: string | null;
  routed_at: string | null;
  notification_sent: boolean;
}

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  PENDING: { bg: 'bg-neutral-800', text: 'text-neutral-400', label: 'Pending' },
  IN_PROGRESS: { bg: 'bg-amber-900/40', text: 'text-amber-400', label: 'In Progress' },
  RESOLVED: { bg: 'bg-green-900/40', text: 'text-green-400', label: 'Resolved' },
  NO_ACTION: { bg: 'bg-red-900/40', text: 'text-red-400', label: 'No Action' },
};

function daysSince(dateStr: string): number {
  return Math.floor((Date.now() - new Date(dateStr).getTime()) / (1000 * 60 * 60 * 24));
}

export function DepartmentRouting({ reportId }: { reportId: string }) {
  const [entries, setEntries] = useState<RoutingEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/routing/report/${reportId}`);
        if (res.ok) {
          const data = await res.json();
          setEntries(data);
        }
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    })();
  }, [reportId]);

  if (loading) return null;
  if (entries.length === 0) return null;

  return (
    <div className="mt-6">
      <h3 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3 flex items-center gap-2">
        <BuildingOffice2Icon className="h-4 w-4" />
        Departments Notified
      </h3>
      <div className="space-y-3">
        {entries.map((entry) => {
          const style = STATUS_STYLES[entry.status] || STATUS_STYLES.PENDING;
          const overdue =
            entry.status === 'PENDING' && entry.routed_at && daysSince(entry.routed_at) > 14;

          return (
            <div
              key={entry.short_name}
              className="p-4 bg-neutral-900 border border-neutral-800 rounded-xl"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-white">{entry.dept_name}</p>
                <span
                  className={`text-xs font-semibold px-2.5 py-1 rounded-full ${style.bg} ${style.text}`}
                >
                  {style.label}
                </span>
              </div>
              {entry.department_response && (
                <p className="text-xs text-neutral-400 italic mt-2 leading-relaxed">
                  "{entry.department_response}"
                </p>
              )}
              {overdue && (
                <p className="text-xs text-amber-400 mt-2 font-medium">
                  ⚠ No response in {daysSince(entry.routed_at!)} days
                </p>
              )}
              {entry.responded_at && (
                <p className="text-xs text-neutral-600 mt-1">
                  Responded {new Date(entry.responded_at).toLocaleDateString()}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
