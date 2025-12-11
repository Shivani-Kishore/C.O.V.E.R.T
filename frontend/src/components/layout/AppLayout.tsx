/**
 * C.O.V.E.R.T - App Layout Component
 */

import { Outlet, NavLink } from 'react-router-dom';
import {
  ShieldCheckIcon,
  HomeIcon,
  DocumentPlusIcon,
  ClipboardDocumentListIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { WalletButton } from '../WalletButton';

const navLinks = [
  { to: '/dashboard', icon: HomeIcon, label: 'Dashboard' },
  { to: '/submit', icon: DocumentPlusIcon, label: 'Submit Report' },
  { to: '/my-reports', icon: ClipboardDocumentListIcon, label: 'My Reports' },
];

export function AppLayout() {
  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-neutral-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <ShieldCheckIcon className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-bold text-neutral-900">
                C.O.V.E.R.T
              </span>
            </div>

            {/* Right section */}
            <div className="flex items-center space-x-4">
              <WalletButton />
            </div>
          </div>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside className="w-64 bg-white border-r border-neutral-200 hidden md:block">
          <nav className="p-4 space-y-2">
            {navLinks.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={({ isActive }) =>
                  `flex items-center px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-neutral-600 hover:bg-neutral-100'
                  }`
                }
              >
                <link.icon className="h-5 w-5 mr-3" />
                <span className="font-medium">{link.label}</span>
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6 lg:p-8 overflow-auto">
          <div className="max-w-6xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-neutral-200 py-4">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-neutral-500">
          <p>C.O.V.E.R.T - Chain for Open and VERified Testimonies</p>
          <p className="mt-1">Secure. Anonymous. Verified.</p>
        </div>
      </footer>
    </div>
  );
}

export default AppLayout;
