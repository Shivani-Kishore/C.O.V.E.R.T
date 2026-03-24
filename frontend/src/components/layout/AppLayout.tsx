/**
 * C.O.V.E.R.T - App Layout with Top Navigation Bar
 */

import { useState } from 'react';
import { Outlet, NavLink, Link } from 'react-router-dom';
import { Disclosure } from '@headlessui/react';
import {
  HomeIcon,
  DocumentPlusIcon,
  ClipboardDocumentListIcon,
  Bars3Icon,
  XMarkIcon,
  ArrowLeftIcon,
  InformationCircleIcon,
  ShieldCheckIcon,
  BuildingOffice2Icon,
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { WalletButton } from '../WalletButton';
import { ProfileButton } from '../ProfileButton';
import { PlatformInfoPanel } from '@/components/PlatformInfoPanel';
import { useCovBalanceStore } from '@/stores/covBalanceStore';
import { API_BASE, IS_DEV } from '@/config';

const ORANGE = '#E84B1A';

export function AppLayout() {
  const [infoOpen, setInfoOpen] = useState(false);
  const [resetting, setResetting] = useState(false);
  const resetCov = useCovBalanceStore((s) => s.resetAll);

  const handleDevReset = async () => {
    if (!window.confirm('Reset test environment?\n\n• All COV balances → 30 (welcome grant)\n• Reputation scores → role defaults\n  (users: 0 | reviewers: 50 | moderators: 90)')) return;
    setResetting(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/reputation/dev-reset`, { method: 'POST' });
      if (!res.ok) throw new Error(await res.text());
      resetCov();
      window.dispatchEvent(new CustomEvent('covert:rep-refresh'));
      toast.success('Test environment reset — COV balances and reputation restored to defaults.');
    } catch (err) {
      toast.error('Reset failed: ' + String(err));
    } finally {
      setResetting(false);
    }
  };

  const navLinks = [
    { to: '/dashboard', icon: HomeIcon, label: 'Dashboard' },
    { to: '/submit', icon: DocumentPlusIcon, label: 'Submit Report' },
    { to: '/my-reports', icon: ClipboardDocumentListIcon, label: 'My Reports' },
    { to: '/accountability', icon: BuildingOffice2Icon, label: 'Accountability' },
    { to: '/privacy-guide', icon: ShieldCheckIcon, label: 'Privacy Guide' },
  ];

  return (
    <div className="min-h-screen bg-black text-white flex flex-col">
      {/* ── Dev Mode Toolbar ── */}
      {IS_DEV && (
        <div className="bg-yellow-950/60 border-b border-yellow-800/40 px-4 py-1.5 flex items-center justify-between gap-4 text-xs sticky top-0 z-50">
          <span className="text-yellow-600 font-mono font-semibold tracking-wide select-none">
            ⚠ DEV MODE
          </span>
          <button
            onClick={handleDevReset}
            disabled={resetting}
            className="text-yellow-500 hover:text-yellow-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {resetting ? 'Resetting…' : 'Reset Test Environment'}
          </button>
        </div>
      )}

      {/* ── Top Navigation Bar ── */}
      <Disclosure as="header" className="bg-neutral-950 border-b border-neutral-800 sticky top-0 z-40">
        {({ open }) => (
          <>
            <div className="px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between h-14 gap-4">

                {/* Left: Brand → Landing Page */}
                <Link
                  to="/"
                  className="flex items-center gap-2 flex-shrink-0 group"
                >
                  <div
                    className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 transition-opacity group-hover:opacity-80"
                    style={{ backgroundColor: ORANGE }}
                  >
                    <ArrowLeftIcon className="h-3.5 w-3.5 text-white" />
                  </div>
                  <span
                    className="text-base font-bold text-white tracking-widest group-hover:opacity-80 transition-opacity"
                    style={{ fontFamily: "'Sora', ui-sans-serif, system-ui, sans-serif" }}
                  >
                    COVERT
                  </span>
                </Link>

                {/* Center: Desktop nav links */}
                <nav className="hidden md:flex items-center gap-1 flex-1 justify-center">

                  {/* Platform Guide button — leftmost, before Dashboard */}
                  <button
                    onClick={() => setInfoOpen(true)}
                    className="flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900 transition-all duration-200"
                  >
                    <InformationCircleIcon className="h-4 w-4 flex-shrink-0" />
                    Platform Guide
                  </button>

                  <div className="w-px h-4 bg-neutral-800 mx-1" />

                  {navLinks.map((link) => (
                    <NavLink
                      key={link.to}
                      to={link.to}
                      className={({ isActive }) =>
                        `flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                          isActive
                            ? 'text-white'
                            : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900'
                        }`
                      }
                      style={({ isActive }) =>
                        isActive
                          ? { backgroundColor: 'rgba(232,75,26,0.12)', color: '#fff' }
                          : {}
                      }
                    >
                      <link.icon className="h-4 w-4 flex-shrink-0" />
                      {link.label}
                    </NavLink>
                  ))}
                </nav>

                {/* Right: Profile + Wallet + Mobile Trigger */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <div className="hidden md:flex items-center gap-2">
                    <ProfileButton />
                    <WalletButton />
                  </div>

                  {/* Mobile hamburger */}
                  <Disclosure.Button className="md:hidden p-2 rounded-lg text-neutral-400 hover:text-white hover:bg-neutral-900 transition-colors">
                    {open
                      ? <XMarkIcon className="h-5 w-5" />
                      : <Bars3Icon className="h-5 w-5" />
                    }
                  </Disclosure.Button>
                </div>
              </div>
            </div>

            {/* Mobile dropdown panel */}
            <Disclosure.Panel className="md:hidden border-t border-neutral-800 bg-neutral-950">
              <div className="px-4 pt-3 pb-4 space-y-1">
                {/* Platform Guide in mobile menu */}
                <button
                  onClick={() => setInfoOpen(true)}
                  className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-neutral-400 hover:text-white hover:bg-neutral-900 transition-all"
                >
                  <InformationCircleIcon className="h-5 w-5 flex-shrink-0" />
                  Platform Guide
                </button>

                {navLinks.map((link) => (
                  <NavLink
                    key={link.to}
                    to={link.to}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all ${
                        isActive
                          ? 'text-white'
                          : 'text-neutral-400 hover:text-white hover:bg-neutral-900'
                      }`
                    }
                    style={({ isActive }) =>
                      isActive
                        ? { backgroundColor: 'rgba(232,75,26,0.12)', borderLeft: `3px solid ${ORANGE}`, paddingLeft: '13px' }
                        : {}
                    }
                  >
                    <link.icon className="h-5 w-5 flex-shrink-0" />
                    {link.label}
                  </NavLink>
                ))}
              </div>
              <div className="px-4 pb-4 flex flex-col gap-2 border-t border-neutral-800 pt-4">
                <ProfileButton />
                <WalletButton />
              </div>
            </Disclosure.Panel>
          </>
        )}
      </Disclosure>

      {/* ── Main Content (full width) ── */}
      <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-auto">
        <Outlet />
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-neutral-800 py-4 bg-neutral-950">
        <div className="px-4 text-center text-sm text-neutral-600">
          <p>C.O.V.E.R.T — Chain for Open and VERified Testimonies</p>
          <p className="mt-1">Secure. Anonymous. Verified.</p>
        </div>
      </footer>

      {/* ── Platform Info Slide-Over ── */}
      <PlatformInfoPanel open={infoOpen} onClose={() => setInfoOpen(false)} />
    </div>
  );
}

export default AppLayout;
