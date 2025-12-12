import React, { useState, useEffect } from 'react';
import { useZKProof } from '../services/zkp/useZKProof';
import toast from 'react-hot-toast';

interface ZKPAuthProps {
  onAuthSuccess: (proof: any, commitment: string, nullifierHash: string) => void;
  onAuthError?: (error: string) => void;
  buttonText?: string;
  className?: string;
}

export function ZKPAuth({
  onAuthSuccess,
  onAuthError,
  buttonText = 'Generate Anonymous Proof',
  className = '',
}: ZKPAuthProps) {
  const { isInitialized, isGenerating, error, secret, generateProof, initializeSecret } = useZKProof();
  const [hasSecret, setHasSecret] = useState(false);

  useEffect(() => {
    if (secret) {
      setHasSecret(true);
    }
  }, [secret]);

  const handleGenerateProof = async () => {
    try {
      const proofOutput = await generateProof();

      if (!proofOutput) {
        const errorMsg = error || 'Failed to generate proof';
        toast.error(errorMsg);
        if (onAuthError) {
          onAuthError(errorMsg);
        }
        return;
      }

      toast.success('Anonymous proof generated successfully!');
      onAuthSuccess(proofOutput.proof, proofOutput.commitment, proofOutput.nullifierHash);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to generate proof';
      toast.error(errorMsg);
      if (onAuthError) {
        onAuthError(errorMsg);
      }
    }
  };

  const handleInitializeSecret = () => {
    const newSecret = initializeSecret();
    toast.success('Anonymous identity created!');
    setHasSecret(true);
  };

  if (!isInitialized) {
    return (
      <div className={`text-gray-500 ${className}`}>
        Initializing ZK proof system...
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {!hasSecret && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-blue-400"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-blue-800">First Time Setup</h3>
              <p className="mt-1 text-sm text-blue-700">
                Create your anonymous identity to submit reports privately. This will be stored
                securely in your browser.
              </p>
              <button
                onClick={handleInitializeSecret}
                className="mt-3 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
              >
                Create Anonymous Identity
              </button>
            </div>
          </div>
        </div>
      )}

      {hasSecret && (
        <div>
          <button
            onClick={handleGenerateProof}
            disabled={isGenerating || !isInitialized}
            className="w-full bg-indigo-600 text-white px-4 py-3 rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium flex items-center justify-center space-x-2"
          >
            {isGenerating ? (
              <>
                <svg
                  className="animate-spin h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                <span>Generating proof...</span>
              </>
            ) : (
              <>
                <svg
                  className="h-5 w-5"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
                <span>{buttonText}</span>
              </>
            )}
          </button>

          <div className="mt-3 text-sm text-gray-600 bg-gray-50 rounded-lg p-3">
            <div className="flex items-start">
              <svg
                className="h-5 w-5 text-green-500 flex-shrink-0"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="ml-2">
                <strong>Privacy protected:</strong> Your proof demonstrates you're human without
                revealing any personal information.
              </p>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          {error}
        </div>
      )}
    </div>
  );
}
