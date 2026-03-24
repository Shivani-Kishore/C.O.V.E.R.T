/**
 * C.O.V.E.R.T - Submit Report Page
 */

import { Link } from 'react-router-dom';
import { ArrowLeftIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import { ReportSubmissionForm } from '@/components/reporter/ReportSubmissionForm';

export function SubmitReport() {
  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <Link
          to="/dashboard"
          className="inline-flex items-center text-sm font-medium text-neutral-500 hover:text-white mb-6 transition-colors"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back to Dashboard
        </Link>

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-white">
              Submit a Report
            </h1>
            <p className="text-neutral-400 mt-2 text-lg">
              Your submission will be encrypted and stored securely on IPFS and blockchain.
            </p>
            <p className="text-neutral-500 mt-2 text-sm">
              For maximum anonymity, read our{' '}
              <Link to="/privacy-guide" className="text-[#E84B1A] hover:underline font-medium">
                Privacy Guide
              </Link>{' '}
              before submitting.
            </p>
          </div>
          <div className="flex items-center text-sm font-semibold px-4 py-2 rounded-full border"
               style={{ color: '#E84B1A', backgroundColor: 'rgba(232,75,26,0.08)', borderColor: 'rgba(232,75,26,0.3)' }}>
            <ShieldCheckIcon className="h-5 w-5 mr-2" />
            End-to-end encrypted
          </div>
        </div>
      </div>

      {/* Form */}
      <ReportSubmissionForm />

      {/* Footer Info */}
      <div className="mt-12 text-center text-sm text-neutral-500 space-y-2 pb-8">
        <p>
          By submitting, you confirm that the information provided is accurate to the best of your knowledge.
        </p>
        <p>
          Need help? Check our{' '}
          <Link to="/help" className="text-neutral-300 hover:text-white font-semibold hover:underline">
            submission guidelines
          </Link>
          .
        </p>
      </div>
    </div>
  );
}

export default SubmitReport;
