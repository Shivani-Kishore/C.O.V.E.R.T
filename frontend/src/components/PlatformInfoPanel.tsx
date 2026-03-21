/**
 * C.O.V.E.R.T - Platform Info Slide-Over Panel
 *
 * Right-side drawer explaining how the platform works:
 * overview, report submission, COV tokens, staking, reputation.
 */

import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import {
  XMarkIcon,
  DocumentPlusIcon,
  CurrencyDollarIcon,
  LockClosedIcon,
  StarIcon,
  ShieldCheckIcon,
  ArrowRightIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

interface Props {
  open: boolean;
  onClose: () => void;
}

interface Section {
  icon: React.ReactNode;
  title: string;
  rows: { label: string; value: string }[];
  prose?: string;
}

const SECTIONS: Section[] = [
  {
    icon: <ShieldCheckIcon className="h-5 w-5" style={{ color: '#E84B1A' }} />,
    title: 'How the Platform Works',
    prose:
      'C.O.V.E.R.T is a decentralised whistleblowing protocol. Reporters submit encrypted evidence, reviewers assess its credibility, and moderators issue a final on-chain verdict. Every decision is transparent and tamper-proof.',
    rows: [
      { label: 'Step 1', value: 'Reporter submits encrypted report and stakes COV tokens' },
      { label: 'Step 2', value: 'At least 1 reviewer assesses the report and sets a decision' },
      { label: 'Step 3', value: 'At least 2 moderators must agree on a final label' },
      { label: 'Step 4', value: 'Verdict is written on-chain; stakes settled automatically' },
    ],
  },
  {
    icon: <DocumentPlusIcon className="h-5 w-5" style={{ color: '#E84B1A' }} />,
    title: 'Report Submission',
    prose:
      'Anyone with a connected wallet can submit a report. Content is encrypted client-side before being pinned to IPFS — only the keccak256 hash is stored on-chain.',
    rows: [
      { label: 'Public report stake', value: '10 COV' },
      { label: 'Private report stake', value: '6 COV' },
      { label: 'Stake purpose', value: 'Disincentivises spam; returned on verified reports' },
      { label: 'Visibility', value: 'Public: hash visible on-chain. Private: hash hidden.' },
    ],
  },
  {
    icon: <CurrencyDollarIcon className="h-5 w-5" style={{ color: '#E84B1A' }} />,
    title: 'COV Tokens',
    prose:
      'COV is the native utility token of the protocol. New wallets receive a one-time welcome grant of 30 COV. Tokens are used to stake on reports, support or challenge submissions, and earn rewards.',
    rows: [
      { label: 'Welcome grant', value: '30 COV (one-time, on first connection)' },
      { label: 'Earn as reviewer', value: 'COV reward per completed review decision' },
      { label: 'Earn as moderator', value: 'COV reward per finalised report' },
      { label: 'Earn as reporter', value: 'Bonus COV if report is verified' },
    ],
  },
  {
    icon: <LockClosedIcon className="h-5 w-5" style={{ color: '#E84B1A' }} />,
    title: 'Staking',
    prose:
      'Staking aligns incentives. Every participant with skin in the game is rewarded for honest behaviour and penalised for dishonest behaviour. Stakes are locked during the review cycle.',
    rows: [
      { label: 'Support a report', value: '1 COV staked — returned if report is verified' },
      { label: 'Challenge a report', value: '3 COV staked — returned if report is rejected' },
      { label: 'Appeal bond', value: '8 COV — returned if appeal is won' },
      { label: 'Slash condition', value: 'Reporter + supporters slashed on False/Manipulated label' },
    ],
  },
  {
    icon: <StarIcon className="h-5 w-5" style={{ color: '#E84B1A' }} />,
    title: 'Reputation Score',
    prose:
      'Reputation reflects a wallet\'s track record on the protocol. It determines role eligibility, reward multipliers, and governance weight.',
    rows: [
      { label: 'Verified report', value: '+8 Rep (reporter)' },
      { label: 'Correct review', value: '+2 Rep (reviewer, aligned with final label)' },
      { label: 'False/Manipulated', value: '-10 Rep + slash penalty for reporter' },
      { label: 'Reviewer badge', value: 'Requires Rep >= 80; deactivates if rep falls below' },
      { label: 'Tier 0', value: 'Rep 0 – 39 (Bronze)' },
      { label: 'Tier 1', value: 'Rep 40 – 79 (Silver)' },
      { label: 'Tier 2', value: 'Rep 80 – 149 (Gold)' },
      { label: 'Tier 3', value: 'Rep 150+ (Diamond)' },
    ],
  },
];

export function PlatformInfoPanel({ open, onClose }: Props) {
  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        {/* Backdrop */}
        <Transition.Child
          as={Fragment}
          enter="ease-in-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in-out duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/60" />
        </Transition.Child>

        {/* Panel */}
        <div className="fixed inset-0 overflow-hidden">
          <div className="absolute inset-0 overflow-hidden">
            <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
              <Transition.Child
                as={Fragment}
                enter="transform transition ease-in-out duration-300"
                enterFrom="translate-x-full"
                enterTo="translate-x-0"
                leave="transform transition ease-in-out duration-200"
                leaveFrom="translate-x-0"
                leaveTo="translate-x-full"
              >
                <Dialog.Panel className="pointer-events-auto w-screen max-w-md">
                  <div className="flex h-full flex-col bg-neutral-950 border-l border-neutral-800 shadow-2xl overflow-y-auto">

                    {/* Header */}
                    <div className="sticky top-0 z-10 bg-neutral-950 border-b border-neutral-800 px-6 py-4 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                          style={{ backgroundColor: 'rgba(232,75,26,0.15)' }}
                        >
                          <InformationCircleIcon className="h-5 w-5" style={{ color: '#E84B1A' }} />
                        </div>
                        <div>
                          <Dialog.Title className="text-base font-bold text-white">
                            Platform Guide
                          </Dialog.Title>
                          <p className="text-xs text-neutral-500">How C.O.V.E.R.T works</p>
                        </div>
                      </div>
                      <button
                        onClick={onClose}
                        className="p-2 rounded-lg text-neutral-500 hover:text-white hover:bg-neutral-800 transition-colors"
                      >
                        <XMarkIcon className="h-5 w-5" />
                      </button>
                    </div>

                    {/* Content */}
                    <div className="flex-1 px-6 py-6 space-y-6">
                      {SECTIONS.map((section, idx) => (
                        <div
                          key={section.title}
                          className="rounded-xl border border-neutral-800 bg-neutral-900/50 overflow-hidden"
                        >
                          {/* Section header */}
                          <div className="flex items-center gap-2.5 px-4 py-3 border-b border-neutral-800 bg-neutral-900">
                            {section.icon}
                            <span className="text-sm font-semibold text-white">{section.title}</span>
                            <span className="ml-auto text-xs text-neutral-600 font-mono">
                              {String(idx + 1).padStart(2, '0')}
                            </span>
                          </div>

                          {/* Prose */}
                          {section.prose && (
                            <p className="px-4 py-3 text-xs text-neutral-400 leading-relaxed border-b border-neutral-800/50">
                              {section.prose}
                            </p>
                          )}

                          {/* Rows */}
                          <div className="divide-y divide-neutral-800/50">
                            {section.rows.map((row) => (
                              <div key={row.label} className="flex items-start gap-3 px-4 py-2.5">
                                <ArrowRightIcon className="h-3.5 w-3.5 text-neutral-600 mt-0.5 flex-shrink-0" />
                                <div className="flex-1 min-w-0">
                                  <span className="text-xs font-medium text-neutral-300">{row.label}</span>
                                  <span className="mx-2 text-neutral-700">—</span>
                                  <span className="text-xs text-neutral-500">{row.value}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}

                      {/* Footer note */}
                      <div className="rounded-xl border border-neutral-800 bg-neutral-900/30 px-4 py-3">
                        <p className="text-xs text-neutral-500 leading-relaxed">
                          All on-chain actions require a wallet transaction. Stakes are held in the CovertProtocol smart contract until the review cycle completes. Your identity is protected through zero-knowledge proofs — only content hashes are visible on-chain.
                        </p>
                      </div>
                    </div>

                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
}

export default PlatformInfoPanel;
