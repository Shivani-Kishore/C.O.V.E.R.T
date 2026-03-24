/**
 * C.O.V.E.R.T - Anonymous Wallet Setup Modal
 * Step-by-step guide for creating a burner wallet.
 */

import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import {
  XMarkIcon,
  WalletIcon,
  ArrowDownTrayIcon,
  KeyIcon,
  CurrencyDollarIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';

const ORANGE = '#E84B1A';

const STEPS = [
  {
    icon: ArrowRightIcon,
    title: 'Open a private/incognito browser window',
    body: 'Open a private/incognito browser window for this setup.',
  },
  {
    icon: ArrowDownTrayIcon,
    title: 'Install MetaMask',
    body: 'Install MetaMask extension if not already installed.',
    link: { label: 'Download MetaMask', href: 'https://metamask.io/download/' },
  },
  {
    icon: KeyIcon,
    title: 'Create a new wallet',
    body: 'Click Create New Wallet \u2014 write down the seed phrase and store it safely. Never use this wallet for anything except C.O.V.E.R.T reports.',
  },
  {
    icon: CurrencyDollarIcon,
    title: 'Get free testnet ETH',
    body: 'Get free testnet ETH from the faucet to cover gas fees.',
    link: { label: 'Base Sepolia Faucet', href: 'https://www.alchemy.com/faucets/base-sepolia' },
  },
  {
    icon: WalletIcon,
    title: 'Connect and submit',
    body: 'Return to this tab and connect your new wallet to submit your report.',
  },
];

interface Props {
  open: boolean;
  onClose: () => void;
}

export function AnonymousWalletModal({ open, onClose }: Props) {
  return (
    <Transition appear show={open} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/70" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-200"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-150"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-lg rounded-2xl border border-neutral-800 bg-neutral-950 p-6 shadow-xl">
                <div className="flex items-center justify-between mb-6">
                  <Dialog.Title className="text-lg font-bold text-white flex items-center gap-2">
                    <WalletIcon className="h-5 w-5" style={{ color: ORANGE }} />
                    Set Up Anonymous Wallet
                  </Dialog.Title>
                  <button
                    onClick={onClose}
                    className="p-1.5 rounded-lg text-neutral-500 hover:text-white hover:bg-neutral-800 transition-colors"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>

                <div className="space-y-4">
                  {STEPS.map((step, i) => (
                    <div key={i} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div
                          className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white flex-shrink-0"
                          style={{ backgroundColor: ORANGE }}
                        >
                          {i + 1}
                        </div>
                        {i < STEPS.length - 1 && (
                          <div className="w-px flex-1 bg-neutral-800 mt-1" />
                        )}
                      </div>
                      <div className="pb-4">
                        <p className="text-sm font-semibold text-white mb-1">{step.title}</p>
                        <p className="text-xs text-neutral-400 leading-relaxed">{step.body}</p>
                        {step.link && (
                          <a
                            href={step.link.href}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 mt-2 text-xs font-medium hover:underline"
                            style={{ color: ORANGE }}
                          >
                            {step.link.label} ↗
                          </a>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                <button
                  onClick={onClose}
                  className="w-full mt-4 px-4 py-2.5 rounded-xl text-sm font-semibold text-white border border-neutral-700 hover:border-neutral-500 transition-colors"
                >
                  Got it
                </button>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}

export default AnonymousWalletModal;
