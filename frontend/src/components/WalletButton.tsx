/**
 * C.O.V.E.R.T - WalletButton Component
 *
 * Wallet connection button with status display
 */

import React, { useState } from 'react';
import { useWeb3 } from '../hooks/useWeb3';
import { useReportStore } from '../stores/reportStore';

interface WalletButtonProps {
  className?: string;
  showBalance?: boolean;
  showNetwork?: boolean;
}

const NETWORK_NAMES: Record<number, string> = {
  1: 'Ethereum',
  8453: 'Base',
  84532: 'Base Sepolia',
  31337: 'Localhost',
  137: 'Polygon',
  80001: 'Mumbai',
};

/**
 * Format address for display (0x1234...5678)
 */
function formatAddress(address: string): string {
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

/**
 * Format balance for display
 */
function formatBalance(balance: string): string {
  const num = parseFloat(balance);
  if (num < 0.0001) return '< 0.0001';
  return num.toFixed(4);
}

export const WalletButton: React.FC<WalletButtonProps> = ({
  className = '',
  showBalance = true,
  showNetwork = true,
}) => {
  const { walletState, isConnecting, error, connect, disconnect } = useWeb3();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const resetDraft = useReportStore((s) => s.resetDraft);
  const setReports = useReportStore((s) => s.setReports);

  const handleConnect = async () => {
    try {
      await connect();
    } catch (err) {
      console.error('Connection failed:', err);
    }
  };

  const handleDisconnect = () => {
    disconnect();
    // Clear any in-progress report draft and cached reports so they don't
    // leak into the UI after disconnecting.
    resetDraft();
    setReports([]);
    setIsDropdownOpen(false);
  };

  // Not connected state
  if (!walletState.connected) {
    return (
      <button
        onClick={handleConnect}
        disabled={isConnecting}
        className={`
          px-4 py-2 rounded-full font-medium transition-all
          ${isConnecting
            ? 'bg-neutral-700 cursor-not-allowed text-neutral-400'
            : 'hover:opacity-90 text-white'
          }
          ${className}
        `}
        style={!isConnecting ? { backgroundColor: '#E84B1A' } : {}}
      >
        {isConnecting ? (
          <span className="flex items-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Connecting...
          </span>
        ) : (
          'Connect Wallet'
        )}
      </button>
    );
  }

  // Connected state
  const networkName = walletState.chainId
    ? NETWORK_NAMES[walletState.chainId] || `Chain ${walletState.chainId}`
    : 'Unknown';

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="flex items-center gap-2 px-4 py-2 rounded-lg bg-neutral-900 border border-neutral-700 hover:border-neutral-500 text-white transition-all"
      >
        {/* Status dot */}
        <span className="w-2 h-2 rounded-full bg-green-500" />

        {/* Address */}
        <span className="font-mono text-sm">
          {walletState.address ? formatAddress(walletState.address) : ''}
        </span>

        {/* Balance */}
        {showBalance && walletState.balance && (
          <span className="text-neutral-500 text-sm">
            {formatBalance(walletState.balance)} ETH
          </span>
        )}

        {/* Dropdown arrow */}
        <svg
          className={`w-4 h-4 text-neutral-500 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown menu */}
      {isDropdownOpen && (
        <div className="absolute right-0 mt-2 w-64 bg-neutral-950 rounded-xl shadow-xl border border-neutral-800 z-50">
          <div className="p-4 border-b border-neutral-800">
            <p className="text-neutral-500 text-xs">Connected Address</p>
            <p className="font-mono text-white text-sm truncate">
              {walletState.address}
            </p>
          </div>

          {showNetwork && (
            <div className="p-4 border-b border-neutral-800">
              <p className="text-neutral-500 text-xs">Network</p>
              <p className="text-white">{networkName}</p>
            </div>
          )}

          {showBalance && walletState.balance && (
            <div className="p-4 border-b border-neutral-800">
              <p className="text-neutral-500 text-xs">Balance</p>
              <p className="text-white">{formatBalance(walletState.balance)} ETH</p>
            </div>
          )}

          <div className="p-2">
            <button
              onClick={handleDisconnect}
              className="w-full px-4 py-2 text-left text-red-400 hover:bg-neutral-900 rounded-lg transition-colors"
            >
              Disconnect
            </button>
          </div>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="absolute right-0 mt-2 p-2 bg-red-950 border border-red-900 text-red-400 text-sm rounded-lg">
          {error}
        </div>
      )}

      {/* Click outside to close */}
      {isDropdownOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsDropdownOpen(false)}
        />
      )}
    </div>
  );
};

export default WalletButton;
