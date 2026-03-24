/**
 * C.O.V.E.R.T - Privacy Guide Page
 * Accessible at /privacy-guide, no wallet required.
 */

import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheckIcon,
  GlobeAltIcon,
  WalletIcon,
  CurrencyDollarIcon,
  ClockIcon,
  ArrowRightOnRectangleIcon,
  ArrowLeftIcon,
} from '@heroicons/react/24/outline';
import { AnonymousWalletModal } from '@/components/AnonymousWalletModal';

const ORANGE = '#E84B1A';

const SECTIONS = [
  {
    icon: GlobeAltIcon,
    title: 'USE TOR BROWSER OR VPN',
    body: 'Your internet provider can see you visited this site. Use Tor Browser (torproject.org) or a trusted VPN (ProtonVPN is free) before submitting any report.',
  },
  {
    icon: WalletIcon,
    title: 'CREATE A BURNER WALLET',
    body: 'Install MetaMask in a separate browser profile. Create a brand new wallet. Never use this wallet for anything else. Never import it into your main browser.',
  },
  {
    icon: CurrencyDollarIcon,
    title: 'FUND YOUR BURNER WALLET PRIVATELY',
    body: 'On testnet: use the Base Sepolia faucet \u2014 it is free and requires no identity. On mainnet: avoid funding from KYC exchanges (Coinbase, WazirX). Use peer-to-peer options.',
  },
  {
    icon: ClockIcon,
    title: 'USE THE SUBMISSION DELAY',
    body: 'In Step 3 of the report form, choose a delay of 24 or 72 hours. This separates the timing of the event from the on-chain timestamp.',
  },
  {
    icon: ArrowRightOnRectangleIcon,
    title: 'AFTER SUBMITTING',
    body: 'Close the browser tab. Do not return to check the report from the same device or wallet for at least 24 hours.',
  },
];

export function PrivacyGuide() {
  const [walletModalOpen, setWalletModalOpen] = useState(false);

  return (
    <div className="max-w-3xl mx-auto py-8 px-4">
      {/* Back link */}
      <Link
        to="/dashboard"
        className="inline-flex items-center text-sm font-medium text-neutral-500 hover:text-white mb-8 transition-colors"
      >
        <ArrowLeftIcon className="h-4 w-4 mr-2" />
        Back to Dashboard
      </Link>

      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ backgroundColor: ORANGE }}
          >
            <ShieldCheckIcon className="h-5 w-5 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white">Privacy Guide</h1>
        </div>
        <p className="text-neutral-400 text-lg">
          Follow these steps to protect your identity when submitting a report.
        </p>
      </div>

      {/* Sections */}
      <div className="space-y-6">
        {SECTIONS.map((section, i) => (
          <div
            key={i}
            className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-6 flex gap-5"
          >
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
              style={{ backgroundColor: 'rgba(232,75,26,0.12)' }}
            >
              <section.icon className="h-5 w-5" style={{ color: ORANGE }} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-wide mb-2">
                {i + 1}. {section.title}
              </h2>
              <p className="text-sm text-neutral-400 leading-relaxed">
                {section.body}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* CTA buttons */}
      <div className="mt-10 flex flex-col sm:flex-row gap-3">
        <button
          onClick={() => setWalletModalOpen(true)}
          className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold text-white transition-colors"
          style={{ backgroundColor: ORANGE }}
        >
          <WalletIcon className="h-4 w-4" />
          Set Up Anonymous Wallet
        </button>
        <Link
          to="/submit"
          className="flex-1 inline-flex items-center justify-center gap-2 px-6 py-3 rounded-xl text-sm font-semibold text-white border border-neutral-700 hover:border-neutral-500 transition-colors"
        >
          Submit a Report
        </Link>
      </div>

      <AnonymousWalletModal open={walletModalOpen} onClose={() => setWalletModalOpen(false)} />
    </div>
  );
}

export default PrivacyGuide;
