/**
 * C.O.V.E.R.T - Submit Report Page
 */

import { Link } from 'react-router-dom';
import { ArrowLeftIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import { ReportSubmissionForm } from '@/components/reporter/ReportSubmissionForm';

export function SubmitReport() {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <Link
          to="/dashboard"
          className="inline-flex items-center text-sm text-neutral-600 hover:text-neutral-900 mb-4"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-1" />
          Back to Dashboard
        </Link>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-neutral-900">Submit a Report</h1>
            <p className="text-neutral-600 mt-1">
              Your submission will be encrypted and stored securely on IPFS and blockchain.
            </p>
          </div>
          <div className="flex items-center text-sm text-green-600 bg-green-50 px-3 py-1 rounded-full">
            <ShieldCheckIcon className="h-4 w-4 mr-1" />
            End-to-end encrypted
          </div>
        </div>
      </div>

      {/* Form */}
      <ReportSubmissionForm />

      {/* Footer Info */}
      <div className="mt-8 text-center text-sm text-neutral-500">
        <p>
          By submitting, you confirm that the information provided is accurate to the best of your knowledge.
        </p>
        <p className="mt-2">
          Need help? Check our{' '}
          <Link to="/help" className="text-primary-600 hover:underline">
            submission guidelines
          </Link>
          .
        </p>
      </div>
    </div>
  );
}

export default SubmitReport;
