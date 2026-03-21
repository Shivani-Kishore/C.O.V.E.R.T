/**
 * C.O.V.E.R.T - Wallet Session Store (Zustand + localStorage)
 *
 * Persists wallet connection state across page refreshes.
 * The session expires after SESSION_DURATION_MS (default 24 h) of inactivity,
 * or immediately when the user explicitly disconnects.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/** How long a session stays alive without explicit disconnect (ms) */
const SESSION_DURATION_MS = 24 * 60 * 60 * 1000; // 24 hours

export interface PersistedWalletSession {
    /** Connected wallet address, or null when disconnected */
    address: string | null;
    /** EVM chain ID, or null */
    chainId: number | null;
    /** ETH balance string as returned by ethers, or null */
    balance: string | null;
    /** Whether the wallet is considered connected */
    connected: boolean;
    /** Unix timestamp (ms) when the session expires; 0 = no active session */
    expiresAt: number;
    /** True if the user deliberately clicked "Disconnect" this session */
    deliberatelyDisconnected: boolean;
}

interface WalletSessionActions {
    /** Persist a successful connection */
    saveSession: (address: string, chainId: number | null, balance: string | null) => void;
    /** Update balance / chain without resetting the session timer */
    updateSession: (updates: Partial<Pick<PersistedWalletSession, 'chainId' | 'balance'>>) => void;
    /** Mark as deliberately disconnected and clear session */
    clearSession: () => void;
    /** Check whether the persisted session is still within the expiry window */
    isSessionValid: () => boolean;
}

type WalletSessionState = PersistedWalletSession & WalletSessionActions;

const INITIAL: PersistedWalletSession = {
    address: null,
    chainId: null,
    balance: null,
    connected: false,
    expiresAt: 0,
    deliberatelyDisconnected: false,
};

export const useWalletSessionStore = create<WalletSessionState>()(
    persist(
        (set, get) => ({
            ...INITIAL,

            saveSession: (address, chainId, balance) => {
                set({
                    address,
                    chainId,
                    balance,
                    connected: true,
                    expiresAt: Date.now() + SESSION_DURATION_MS,
                    deliberatelyDisconnected: false,
                });
                // Also keep the plain key that other code reads
                localStorage.setItem('wallet_address', address);
                localStorage.removeItem('covert_wallet_logged_out');
            },

            updateSession: (updates) => {
                const { expiresAt } = get();
                // Only update if session is still alive
                if (expiresAt > Date.now()) {
                    set(updates);
                }
            },

            clearSession: () => {
                set({ ...INITIAL, deliberatelyDisconnected: true });
                localStorage.removeItem('wallet_address');
                localStorage.setItem('covert_wallet_logged_out', '1');
            },

            isSessionValid: () => {
                const { connected, expiresAt, deliberatelyDisconnected } = get();
                if (deliberatelyDisconnected) return false;
                if (!connected || expiresAt === 0) return false;
                return Date.now() < expiresAt;
            },
        }),
        {
            name: 'covert-wallet-session-v1',
            // Only persist the session data, not the action functions
            partialize: (state) => ({
                address: state.address,
                chainId: state.chainId,
                balance: state.balance,
                connected: state.connected,
                expiresAt: state.expiresAt,
                deliberatelyDisconnected: state.deliberatelyDisconnected,
            }),
        }
    )
);
