/**
 * C.O.V.E.R.T - COV Token Balance Store
 *
 * Tracks per-wallet COV balances in dev mode, persisted to localStorage.
 * Stake amounts match the platform guide values.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const STAKE_AMOUNTS = {
  private: 6,
  moderated: 8,
  public: 10,
} as const;

/** Fraction of stake returned early when review majority votes REVIEW_PASSED */
export const PARTIAL_RETURN_RATE = 0.25;
/** Fraction of stake settled at moderation finalization (CORROBORATED / NEEDS_EVIDENCE / DISPUTED) */
export const FINAL_SETTLEMENT_RATE = 0.75;

export type VisibilityKey = keyof typeof STAKE_AMOUNTS;

const INITIAL_BALANCE = 30;

interface CovBalanceState {
  /** Per-address balance map (lowercase address → COV amount) */
  balances: Record<string, number>;

  /** Get current balance for an address (defaults to 30 for new wallets) */
  getBalance: (address: string) => number;

  /** Deduct the stake for a given visibility choice. Returns amount deducted. */
  deductStake: (address: string, visibility: VisibilityKey) => number;

  /** Add COV to an address (for rewards / testing) */
  addBalance: (address: string, amount: number) => void;

  /** Set the exact COV balance for an address (used to sync from on-chain state) */
  setBalance: (address: string, amount: number) => void;

  /** Reset all stored balances so every wallet reverts to the welcome-grant default */
  resetAll: () => void;
}

export const useCovBalanceStore = create<CovBalanceState>()(
  persist(
    (set, get) => ({
      balances: {},

      getBalance: (address: string) => {
        const key = address.toLowerCase();
        const stored = get().balances[key];
        return stored !== undefined ? stored : INITIAL_BALANCE;
      },

      deductStake: (address: string, visibility: VisibilityKey) => {
        const key = address.toLowerCase();
        const amount = STAKE_AMOUNTS[visibility];
        set((state) => {
          const current =
            state.balances[key] !== undefined
              ? state.balances[key]
              : INITIAL_BALANCE;
          return {
            balances: {
              ...state.balances,
              [key]: Math.max(0, current - amount),
            },
          };
        });
        return amount;
      },

      setBalance: (address: string, amount: number) => {
        const key = address.toLowerCase();
        set((state) => ({
          balances: { ...state.balances, [key]: amount },
        }));
      },

      addBalance: (address: string, amount: number) => {
        const key = address.toLowerCase();
        set((state) => {
          // Use 0 as the base when balance hasn't been set yet (not INITIAL_BALANCE)
          // to prevent inflation when stake returns arrive before on-chain sync.
          // getBalance() still shows INITIAL_BALANCE for display purposes.
          const current = state.balances[key] ?? 0;
          return {
            balances: {
              ...state.balances,
              [key]: current + amount,
            },
          };
        });
      },

      resetAll: () => {
        set({ balances: {} });
      },
    }),
    { name: 'covert-cov-balances-v2' }
  )
);
