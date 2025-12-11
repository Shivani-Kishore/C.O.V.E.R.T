/**
 * C.O.V.E.R.T - Reporter Dashboard Page
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  DocumentPlusIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline';
import { useReportStore, type ReportAnalytics } from '@/stores/reportStore';
import { ReportCard } from '@/components/reporter/ReportCard';

export function ReporterDashboard() {
  const [analytics, setAnalytics] = useState<ReportAnalytics | null>(null);
  const { reports, setReports, setLoading, isLoading } = useReportStore();

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token');

        // Fetch reports
        const reportsRes = await fetch('/api/v1/reports?limit=5', {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (reportsRes.ok) {
          const data = await reportsRes.json();
          setReports(data.items || []);
        }

        // Calculate analytics from reports
        const all = reports;
        setAnalytics({
          totalReports: all.length,
          pendingReports: all.filter(r => r.status === 'pending').length,
          verifiedReports: all.filter(r => r.status === 'verified').length,
          rejectedReports: all.filter(r => r.status === 'rejected').length,
          averageVerificationTime: 24, // Mock - would come from backend
        });
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [setReports, setLoading]);

  const recentReports = reports.slice(0, 5);

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-800 rounded-xl p-6 text-white">
        <h1 className="text-2xl font-bold mb-2">Welcome to C.O.V.E.R.T</h1>
        <p className="text-primary-100 mb-4">
          Your secure platform for confidential reporting. All submissions are encrypted and verified on-chain.
        </p>
        <div className="flex gap-4">
          <Link
            to="/submit"
            className="inline-flex items-center px-4 py-2 bg-white text-primary-700 rounded-lg font-medium hover:bg-primary-50 transition-colors"
          >
            <DocumentPlusIcon className="h-5 w-5 mr-2" />
            Submit New Report
          </Link>
          <Link
            to="/my-reports"
            className="inline-flex items-center px-4 py-2 bg-primary-700 text-white rounded-lg font-medium hover:bg-primary-800 transition-colors"
          >
            <ClipboardDocumentListIcon className="h-5 w-5 mr-2" />
            View My Reports
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral-500">Total Reports</p>
              <p className="text-3xl font-bold text-neutral-900">{analytics?.totalReports || 0}</p>
            </div>
            <div className="p-3 bg-primary-100 rounded-full">
              <ChartBarIcon className="h-6 w-6 text-primary-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral-500">Pending Review</p>
              <p className="text-3xl font-bold text-yellow-600">{analytics?.pendingReports || 0}</p>
            </div>
            <div className="p-3 bg-yellow-100 rounded-full">
              <ClockIcon className="h-6 w-6 text-yellow-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral-500">Verified</p>
              <p className="text-3xl font-bold text-green-600">{analytics?.verifiedReports || 0}</p>
            </div>
            <div className="p-3 bg-green-100 rounded-full">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg border border-neutral-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-neutral-500">Avg. Review Time</p>
              <p className="text-3xl font-bold text-neutral-900">{analytics?.averageVerificationTime || 0}h</p>
            </div>
            <div className="p-3 bg-neutral-100 rounded-full">
              <ArrowTrendingUpIcon className="h-6 w-6 text-neutral-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-neutral-200">
            <div className="p-4 border-b border-neutral-200 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-neutral-900">Recent Submissions</h2>
              <Link to="/my-reports" className="text-sm text-primary-600 hover:text-primary-700">
                View All
              </Link>
            </div>
            <div className="p-4">
              {isLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="animate-pulse bg-neutral-100 rounded-lg h-20" />
                  ))}
                </div>
              ) : recentReports.length > 0 ? (
                <div className="space-y-3">
                  {recentReports.map((report) => (
                    <ReportCard key={report.id} report={report} compact />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <ClipboardDocumentListIcon className="h-12 w-12 text-neutral-300 mx-auto mb-3" />
                  <p className="text-neutral-500">No reports yet</p>
                  <Link
                    to="/submit"
                    className="inline-flex items-center mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    Submit Your First Report
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Security Info */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg border border-neutral-200 p-6">
            <h3 className="text-lg font-semibold text-neutral-900 mb-4">Security Status</h3>
            <div className="space-y-4">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-full mr-3">
                  <ShieldCheckIcon className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-neutral-900">Encryption Active</p>
                  <p className="text-sm text-neutral-500">AES-256-GCM</p>
                </div>
              </div>
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-full mr-3">
                  <CheckCircleIcon className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-neutral-900">Blockchain Connected</p>
                  <p className="text-sm text-neutral-500">Polygon Mumbai</p>
                </div>
              </div>
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-full mr-3">
                  <CheckCircleIcon className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-neutral-900">IPFS Storage</p>
                  <p className="text-sm text-neutral-500">Distributed & Encrypted</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
            <div className="flex items-start">
              <ExclamationTriangleIcon className="h-5 w-5 text-blue-500 mt-0.5 mr-3" />
              <div>
                <h3 className="font-medium text-blue-900">Privacy Reminder</h3>
                <p className="text-sm text-blue-700 mt-1">
                  Your identity is protected through zero-knowledge proofs.
                  Always use a secure network when submitting sensitive reports.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ReporterDashboard;
