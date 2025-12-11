/**
 * C.O.V.E.R.T - Report Submission Form Component
 * Multi-step form with encryption, IPFS upload, and blockchain commitment
 */

import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckIcon,
  LockClosedIcon,
  CloudArrowUpIcon,
  CubeIcon,
  DocumentCheckIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  EyeIcon,
  EyeSlashIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { useReportStore, type ReportCategory, type ReportVisibility } from '@/stores/reportStore';
import { FileUpload } from './FileUpload';
import { encryptionService } from '@/services/encryption';
import { ipfsService } from '@/services/ipfs';
import { useWeb3 } from '@/hooks/useWeb3';

interface FormErrors {
  category?: string;
  title?: string;
  description?: string;
  visibility?: string;
}

const CATEGORIES: { value: ReportCategory; label: string; description: string }[] = [
  { value: 'corruption', label: 'Corruption', description: 'Bribery, embezzlement, abuse of power' },
  { value: 'fraud', label: 'Fraud', description: 'Financial fraud, scams, deceptive practices' },
  { value: 'safety', label: 'Safety Violation', description: 'Workplace safety, product safety issues' },
  { value: 'environment', label: 'Environmental', description: 'Pollution, illegal dumping, environmental damage' },
  { value: 'human_rights', label: 'Human Rights', description: 'Discrimination, harassment, rights violations' },
  { value: 'other', label: 'Other', description: 'Other whistleblowing matters' },
];

const VISIBILITY_OPTIONS: { value: ReportVisibility; label: string; description: string; icon: React.ElementType }[] = [
  {
    value: 'private',
    label: 'Private',
    description: 'Only you can access this report. Use for personal records.',
    icon: EyeSlashIcon,
  },
  {
    value: 'moderated',
    label: 'Moderated',
    description: 'Moderators review before public access. Recommended for most reports.',
    icon: ShieldCheckIcon,
  },
  {
    value: 'public',
    label: 'Public',
    description: 'Immediately visible to everyone after blockchain confirmation.',
    icon: EyeIcon,
  },
];

const STEPS = [
  { id: 1, name: 'Details', description: 'Category and description' },
  { id: 2, name: 'Attachments', description: 'Supporting files' },
  { id: 3, name: 'Visibility', description: 'Privacy settings' },
  { id: 4, name: 'Review', description: 'Confirm and submit' },
];

export function ReportSubmissionForm() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [errors, setErrors] = useState<FormErrors>({});

  const {
    draft,
    updateDraft,
    resetDraft,
    submissionProgress,
    setSubmissionProgress,
    resetSubmission,
    addReport,
  } = useReportStore();

  const { commitReport, isConnected, connect, walletState } = useWeb3();

  const validateStep = useCallback((step: number): boolean => {
    const newErrors: FormErrors = {};

    switch (step) {
      case 1:
        if (!draft.category) {
          newErrors.category = 'Please select a category';
        }
        if (!draft.title || draft.title.length < 10) {
          newErrors.title = 'Title must be at least 10 characters';
        }
        if (!draft.description || draft.description.length < 50) {
          newErrors.description = 'Description must be at least 50 characters';
        }
        break;
      case 3:
        if (!draft.visibility) {
          newErrors.visibility = 'Please select a visibility option';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [draft]);

  const handleNext = useCallback(() => {
    if (validateStep(currentStep)) {
      setCurrentStep((prev) => Math.min(prev + 1, 4));
    }
  }, [currentStep, validateStep]);

  const handleBack = useCallback(() => {
    setCurrentStep((prev) => Math.max(prev - 1, 1));
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!isConnected) {
      toast.error('Please connect your wallet first');
      await connect();
      return;
    }

    try {
      // Step 1: Encrypt data
      setSubmissionProgress({
        step: 'encrypting',
        progress: 10,
        message: 'Encrypting your report...',
      });

      const reportData = {
        category: draft.category,
        title: draft.title,
        description: draft.description,
        visibility: draft.visibility,
        timestamp: new Date().toISOString(),
      };

      const encryptedReport = await encryptionService.encryptReport(reportData);

      // Step 2: Upload to IPFS
      setSubmissionProgress({
        step: 'uploading',
        progress: 40,
        message: 'Uploading to IPFS...',
      });

      const ipfsResult = await ipfsService.uploadEncrypted(
        new Blob([JSON.stringify(encryptedReport)], { type: 'application/json' })
      );

      if (!ipfsResult.success || !ipfsResult.cid) {
        throw new Error(ipfsResult.error || 'IPFS upload failed');
      }

      // Step 3: Commit to blockchain
      setSubmissionProgress({
        step: 'committing',
        progress: 70,
        message: 'Committing to blockchain...',
      });

      // Calculate CID hash for smart contract
      const cidHash = await encryptionService.hashCID(ipfsResult.cid);
      const visibilityInt = draft.visibility === 'private' ? 0 : draft.visibility === 'moderated' ? 1 : 2;

      const txResult = await commitReport(cidHash, visibilityInt);

      if (!txResult.success) {
        throw new Error(txResult.error || 'Blockchain commitment failed');
      }

      // Step 4: Submit to backend
      setSubmissionProgress({
        step: 'submitting',
        progress: 90,
        message: 'Finalizing submission...',
      });

      const response = await fetch('/api/v1/reports', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          cid: ipfsResult.cid,
          cidHash: cidHash,
          txHash: txResult.transactionHash,
          category: draft.category,
          visibility: visibilityInt,
          sizeBytes: encryptedReport.encryptedData.length,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit report to backend');
      }

      const result = await response.json();

      // Add to local store
      addReport({
        id: result.id,
        commitmentHash: cidHash,
        ipfsCid: ipfsResult.cid,
        transactionHash: txResult.transactionHash || '',
        category: draft.category as ReportCategory,
        title: draft.title,
        status: 'pending',
        visibility: draft.visibility,
        fileSize: encryptedReport.encryptedData.length,
        submittedAt: new Date().toISOString(),
      });

      setSubmissionProgress({
        step: 'complete',
        progress: 100,
        message: 'Report submitted successfully!',
      });

      toast.success('Report submitted successfully!');

      // Reset and navigate
      setTimeout(() => {
        resetDraft();
        resetSubmission();
        navigate('/my-reports');
      }, 2000);

    } catch (error) {
      console.error('Submission error:', error);
      setSubmissionProgress({
        step: 'error',
        progress: 0,
        message: 'Submission failed',
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      });
      toast.error(error instanceof Error ? error.message : 'Submission failed');
    }
  }, [
    isConnected,
    connect,
    draft,
    setSubmissionProgress,
    commitReport,
    addReport,
    resetDraft,
    resetSubmission,
    navigate,
  ]);

  const renderStepIndicator = () => (
    <nav aria-label="Progress" className="mb-8">
      <ol className="flex items-center">
        {STEPS.map((step, index) => (
          <li key={step.id} className={`flex-1 ${index !== STEPS.length - 1 ? 'pr-8' : ''}`}>
            <div className="flex items-center">
              <div
                className={`
                  flex items-center justify-center w-10 h-10 rounded-full border-2
                  ${currentStep > step.id
                    ? 'bg-primary-600 border-primary-600 text-white'
                    : currentStep === step.id
                      ? 'border-primary-600 text-primary-600'
                      : 'border-neutral-300 text-neutral-400'
                  }
                `}
              >
                {currentStep > step.id ? (
                  <CheckIcon className="h-5 w-5" />
                ) : (
                  <span>{step.id}</span>
                )}
              </div>
              {index !== STEPS.length - 1 && (
                <div
                  className={`
                    flex-1 h-0.5 ml-4
                    ${currentStep > step.id ? 'bg-primary-600' : 'bg-neutral-200'}
                  `}
                />
              )}
            </div>
            <div className="mt-2">
              <p className={`text-sm font-medium ${currentStep >= step.id ? 'text-neutral-900' : 'text-neutral-400'}`}>
                {step.name}
              </p>
              <p className="text-xs text-neutral-500">{step.description}</p>
            </div>
          </li>
        ))}
      </ol>
    </nav>
  );

  const renderStep1 = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-neutral-900">Report Details</h2>

      {/* Category Selection */}
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-3">
          Category <span className="text-red-500">*</span>
        </label>
        <div className="grid grid-cols-2 gap-3">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.value}
              type="button"
              onClick={() => updateDraft({ category: cat.value })}
              className={`
                p-4 text-left border rounded-lg transition-colors
                ${draft.category === cat.value
                  ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-500'
                  : 'border-neutral-200 hover:border-neutral-300'
                }
              `}
            >
              <p className="font-medium text-neutral-900">{cat.label}</p>
              <p className="text-xs text-neutral-500 mt-1">{cat.description}</p>
            </button>
          ))}
        </div>
        {errors.category && (
          <p className="mt-2 text-sm text-red-600">{errors.category}</p>
        )}
      </div>

      {/* Title */}
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-2">
          Title <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={draft.title}
          onChange={(e) => updateDraft({ title: e.target.value })}
          placeholder="Brief summary of the issue"
          maxLength={200}
          className={`
            w-full px-4 py-3 border rounded-lg
            focus:ring-2 focus:ring-primary-500 focus:border-transparent
            ${errors.title ? 'border-red-500' : 'border-neutral-300'}
          `}
        />
        <div className="flex justify-between mt-1">
          {errors.title ? (
            <p className="text-sm text-red-600">{errors.title}</p>
          ) : (
            <p className="text-sm text-neutral-500">Minimum 10 characters</p>
          )}
          <p className="text-sm text-neutral-400">{draft.title.length}/200</p>
        </div>
      </div>

      {/* Description */}
      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-2">
          Description <span className="text-red-500">*</span>
        </label>
        <textarea
          value={draft.description}
          onChange={(e) => updateDraft({ description: e.target.value })}
          placeholder="Provide detailed information about the issue..."
          rows={8}
          maxLength={5000}
          className={`
            w-full px-4 py-3 border rounded-lg resize-none
            focus:ring-2 focus:ring-primary-500 focus:border-transparent
            ${errors.description ? 'border-red-500' : 'border-neutral-300'}
          `}
        />
        <div className="flex justify-between mt-1">
          {errors.description ? (
            <p className="text-sm text-red-600">{errors.description}</p>
          ) : (
            <p className="text-sm text-neutral-500">Minimum 50 characters</p>
          )}
          <p className="text-sm text-neutral-400">{draft.description.length}/5000</p>
        </div>
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-neutral-900">Attachments (Optional)</h2>
      <p className="text-neutral-600">
        Upload supporting documents, images, or videos. All files are encrypted before upload.
      </p>

      <FileUpload
        maxFiles={5}
        maxSize={100 * 1024 * 1024}
        showEncryptionStatus
      />

      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-start">
          <InformationCircleIcon className="h-5 w-5 text-blue-500 mt-0.5 mr-3" />
          <div className="text-sm text-blue-700">
            <p className="font-medium">Privacy Notice</p>
            <p className="mt-1">
              Files are encrypted on your device before being uploaded. Even platform operators cannot access your unencrypted data.
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-neutral-900">Privacy Settings</h2>
      <p className="text-neutral-600">
        Choose who can access your report. You can change this later.
      </p>

      <div className="space-y-3">
        {VISIBILITY_OPTIONS.map((option) => {
          const Icon = option.icon;
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => updateDraft({ visibility: option.value })}
              className={`
                w-full p-4 text-left border rounded-lg transition-colors flex items-start
                ${draft.visibility === option.value
                  ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-500'
                  : 'border-neutral-200 hover:border-neutral-300'
                }
              `}
            >
              <Icon className={`h-6 w-6 mt-0.5 mr-3 ${
                draft.visibility === option.value ? 'text-primary-600' : 'text-neutral-400'
              }`} />
              <div>
                <p className="font-medium text-neutral-900">{option.label}</p>
                <p className="text-sm text-neutral-500 mt-1">{option.description}</p>
              </div>
            </button>
          );
        })}
      </div>

      <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex items-start">
          <ShieldCheckIcon className="h-5 w-5 text-green-500 mt-0.5 mr-3" />
          <div className="text-sm text-green-700">
            <p className="font-medium">Your Identity is Protected</p>
            <p className="mt-1">
              Your identity is protected through zero-knowledge proofs. Even moderators cannot see who submitted this report.
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold text-neutral-900">Review & Submit</h2>

      {/* Summary Card */}
      <div className="bg-neutral-50 rounded-lg p-6 space-y-4">
        <div>
          <p className="text-sm text-neutral-500">Category</p>
          <p className="font-medium text-neutral-900">
            {CATEGORIES.find((c) => c.value === draft.category)?.label || 'Not selected'}
          </p>
        </div>

        <div>
          <p className="text-sm text-neutral-500">Title</p>
          <p className="font-medium text-neutral-900">{draft.title || 'Not provided'}</p>
        </div>

        <div>
          <p className="text-sm text-neutral-500">Description</p>
          <p className="text-neutral-900 text-sm whitespace-pre-wrap">
            {draft.description.length > 300
              ? `${draft.description.substring(0, 300)}...`
              : draft.description || 'Not provided'}
          </p>
        </div>

        <div>
          <p className="text-sm text-neutral-500">Attachments</p>
          <p className="font-medium text-neutral-900">
            {draft.files.length} file(s)
          </p>
        </div>

        <div>
          <p className="text-sm text-neutral-500">Visibility</p>
          <p className="font-medium text-neutral-900">
            {VISIBILITY_OPTIONS.find((v) => v.value === draft.visibility)?.label || 'Not selected'}
          </p>
        </div>
      </div>

      {/* Wallet Status */}
      {!isConnected && (
        <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start">
            <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mt-0.5 mr-3" />
            <div className="text-sm text-yellow-700">
              <p className="font-medium">Wallet Not Connected</p>
              <p className="mt-1">
                Please connect your wallet to submit the report to the blockchain.
              </p>
              <button
                onClick={connect}
                className="mt-2 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700"
              >
                Connect Wallet
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Submission Progress */}
      {submissionProgress.step !== 'idle' && (
        <div className="p-4 bg-white border border-neutral-200 rounded-lg">
          <div className="flex items-center mb-3">
            {submissionProgress.step === 'encrypting' && <LockClosedIcon className="h-5 w-5 text-primary-500 mr-2 animate-pulse" />}
            {submissionProgress.step === 'uploading' && <CloudArrowUpIcon className="h-5 w-5 text-primary-500 mr-2 animate-pulse" />}
            {submissionProgress.step === 'committing' && <CubeIcon className="h-5 w-5 text-primary-500 mr-2 animate-pulse" />}
            {submissionProgress.step === 'submitting' && <DocumentCheckIcon className="h-5 w-5 text-primary-500 mr-2 animate-pulse" />}
            {submissionProgress.step === 'complete' && <CheckIcon className="h-5 w-5 text-green-500 mr-2" />}
            {submissionProgress.step === 'error' && <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mr-2" />}
            <span className={`font-medium ${submissionProgress.step === 'error' ? 'text-red-600' : 'text-neutral-900'}`}>
              {submissionProgress.message}
            </span>
          </div>
          <div className="w-full bg-neutral-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${
                submissionProgress.step === 'error' ? 'bg-red-500' : 'bg-primary-600'
              }`}
              style={{ width: `${submissionProgress.progress}%` }}
            />
          </div>
          {submissionProgress.error && (
            <p className="mt-2 text-sm text-red-600">{submissionProgress.error}</p>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className="max-w-3xl mx-auto">
      {renderStepIndicator()}

      <div className="bg-white rounded-lg border border-neutral-200 shadow-sm p-6">
        {currentStep === 1 && renderStep1()}
        {currentStep === 2 && renderStep2()}
        {currentStep === 3 && renderStep3()}
        {currentStep === 4 && renderStep4()}

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8 pt-6 border-t border-neutral-200">
          <button
            type="button"
            onClick={handleBack}
            disabled={currentStep === 1}
            className={`
              px-6 py-2 rounded-lg font-medium transition-colors
              ${currentStep === 1
                ? 'bg-neutral-100 text-neutral-400 cursor-not-allowed'
                : 'bg-neutral-200 text-neutral-700 hover:bg-neutral-300'
              }
            `}
          >
            Back
          </button>

          {currentStep < 4 ? (
            <button
              type="button"
              onClick={handleNext}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
            >
              Next
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={submissionProgress.step !== 'idle' && submissionProgress.step !== 'error'}
              className={`
                px-6 py-2 rounded-lg font-medium transition-colors
                ${submissionProgress.step !== 'idle' && submissionProgress.step !== 'error'
                  ? 'bg-neutral-400 text-white cursor-not-allowed'
                  : 'bg-primary-600 text-white hover:bg-primary-700'
                }
              `}
            >
              Submit Report
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ReportSubmissionForm;
