/**
 * C.O.V.E.R.T - Review Decision Store
 *
 * Tracks reviewer vote tallies per report (dev mode, persisted to localStorage).
 * Used to determine when a majority of reviewers have voted REVIEW_PASSED so
 * the reporter's 25% partial stake return can be triggered.
 * Also tracks whether the 25% partial return and 75% final settlement have been
 * applied for each (reportId, walletAddress) pair to prevent double-crediting.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ReviewEntry {
  passVotes: number;
  totalVotes: number;
  /** walletAddress (lowercase) → whether partial return has been applied */
  partialReturnApplied: Record<string, boolean>;
  /** walletAddress (lowercase) → whether final settlement has been applied */
  finalSettlementApplied: Record<string, boolean>;
}

interface ReviewDecisionState {
  /** reportId (string) → ReviewEntry */
  decisions: Record<string, ReviewEntry>;

  /**
   * Call after a reviewer submits a decision on-chain.
   * Increments passVotes only for REVIEW_PASSED; always increments totalVotes.
   */
  recordDecision(
    reportId: string,
    decision: 'REVIEW_PASSED' | 'NEEDS_EVIDENCE' | 'REJECT_SPAM'
  ): void;

  /** Returns true when passVotes > totalVotes / 2 (simple majority). */
  isMajorityPassed(reportId: string): boolean;

  markPartialReturnApplied(reportId: string, address: string): void;
  isPartialReturnApplied(reportId: string, address: string): boolean;

  markFinalSettlementApplied(reportId: string, address: string): void;
  isFinalSettlementApplied(reportId: string, address: string): boolean;
}

export const useReviewDecisionStore = create<ReviewDecisionState>()(
  persist(
    (set, get) => ({
      decisions: {},

      recordDecision: (reportId, decision) => {
        set((state) => {
          const existing = state.decisions[reportId] ?? {
            passVotes: 0,
            totalVotes: 0,
            partialReturnApplied: {},
            finalSettlementApplied: {},
          };
          return {
            decisions: {
              ...state.decisions,
              [reportId]: {
                ...existing,
                passVotes:
                  decision === 'REVIEW_PASSED'
                    ? existing.passVotes + 1
                    : existing.passVotes,
                totalVotes: existing.totalVotes + 1,
              },
            },
          };
        });
      },

      isMajorityPassed: (reportId) => {
        const entry = get().decisions[reportId];
        if (!entry || entry.totalVotes === 0) return false;
        return entry.passVotes > entry.totalVotes / 2;
      },

      markPartialReturnApplied: (reportId, address) => {
        const key = address.toLowerCase();
        set((state) => {
          const existing = state.decisions[reportId] ?? {
            passVotes: 0,
            totalVotes: 0,
            partialReturnApplied: {},
            finalSettlementApplied: {},
          };
          return {
            decisions: {
              ...state.decisions,
              [reportId]: {
                ...existing,
                partialReturnApplied: { ...existing.partialReturnApplied, [key]: true },
              },
            },
          };
        });
      },

      isPartialReturnApplied: (reportId, address) => {
        const key = address.toLowerCase();
        return get().decisions[reportId]?.partialReturnApplied?.[key] ?? false;
      },

      markFinalSettlementApplied: (reportId, address) => {
        const key = address.toLowerCase();
        set((state) => {
          const existing = state.decisions[reportId] ?? {
            passVotes: 0,
            totalVotes: 0,
            partialReturnApplied: {},
            finalSettlementApplied: {},
          };
          return {
            decisions: {
              ...state.decisions,
              [reportId]: {
                ...existing,
                finalSettlementApplied: { ...existing.finalSettlementApplied, [key]: true },
              },
            },
          };
        });
      },

      isFinalSettlementApplied: (reportId, address) => {
        const key = address.toLowerCase();
        return get().decisions[reportId]?.finalSettlementApplied?.[key] ?? false;
      },
    }),
    { name: 'covert-review-decisions-v1' }
  )
);
