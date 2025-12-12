/**
 * C.O.V.E.R.T - Moderation State Management (Zustand)
 */

import { create } from 'zustand';

// Types
export type ModerationAction = 'review_started' | 'request_info' | 'verified' | 'rejected' | 'escalated';
export type ModerationDecision = 'accept' | 'reject' | 'need_info' | 'escalate';

export interface QueueReport {
  id: string;
  cid: string;
  cid_hash: string;
  category: string;
  status: string;
  visibility: number;
  size_bytes: number;
  verification_score?: number;
  risk_level?: 'low' | 'medium' | 'high' | 'critical';
  submitted_at: string;
}

export interface ModerationRecord {
  id: string;
  report_id: string;
  action: ModerationAction;
  decision?: ModerationDecision;
  created_at: string;
  completed_at?: string;
  time_spent_seconds?: number;
}

export interface ModeratorStats {
  moderator_id: string;
  wallet_address: string;
  reputation_score: number;
  tier: 'bronze' | 'silver' | 'gold' | 'platinum';
  total_reviews: number;
  accurate_reviews: number;
  disputed_reviews: number;
  accuracy_rate: number;
  period_days: number;
  reviews_in_period: number;
  decisions: Record<string, number>;
  average_review_time_seconds: number;
  is_active: boolean;
  is_suspended: boolean;
}

export interface QueueSummary {
  total_pending: number;
  by_risk_level: Record<string, number>;
  by_category: Record<string, number>;
  average_wait_time_hours: number;
  oldest_report_age_hours: number;
}

export interface ReviewState {
  report_id: string | null;
  started_at: number | null;
  notes: string;
}

interface ModerationState {
  // Queue
  queue: QueueReport[];
  queueSummary: QueueSummary | null;
  isLoadingQueue: boolean;

  // Current review
  currentReview: ReviewState;

  // History
  history: ModerationRecord[];
  isLoadingHistory: boolean;

  // Stats
  stats: ModeratorStats | null;
  isLoadingStats: boolean;

  // Filters
  filters: {
    category?: string;
    risk_level?: string;
  };

  // Error
  error: string | null;

  // Actions - Queue
  setQueue: (queue: QueueReport[]) => void;
  setQueueSummary: (summary: QueueSummary) => void;
  fetchQueue: (filters?: { category?: string; risk_level?: string }) => Promise<void>;
  fetchQueueSummary: () => Promise<void>;

  // Actions - Review
  startReview: (report_id: string) => void;
  stopReview: () => void;
  updateNotes: (notes: string) => void;
  getReviewDuration: () => number;

  // Actions - History
  setHistory: (history: ModerationRecord[]) => void;
  fetchHistory: () => Promise<void>;

  // Actions - Stats
  setStats: (stats: ModeratorStats) => void;
  fetchStats: (period_days?: number) => Promise<void>;

  // Actions - Filters
  setFilters: (filters: { category?: string; risk_level?: string }) => void;

  // Actions - Error
  setError: (error: string | null) => void;

  // Actions - Loading
  setLoadingQueue: (loading: boolean) => void;
  setLoadingHistory: (loading: boolean) => void;
  setLoadingStats: (loading: boolean) => void;
}

export const useModerationStore = create<ModerationState>()((set, get) => ({
  // Initial state
  queue: [],
  queueSummary: null,
  isLoadingQueue: false,

  currentReview: {
    report_id: null,
    started_at: null,
    notes: '',
  },

  history: [],
  isLoadingHistory: false,

  stats: null,
  isLoadingStats: false,

  filters: {},

  error: null,

  // Queue actions
  setQueue: (queue) => set({ queue }),

  setQueueSummary: (queueSummary) => set({ queueSummary }),

  fetchQueue: async (filters) => {
    set({ isLoadingQueue: true, error: null });

    try {
      const params = new URLSearchParams();
      if (filters?.category) params.append('category', filters.category);
      if (filters?.risk_level) params.append('risk_level', filters.risk_level);

      const moderatorId = localStorage.getItem('moderator_id');
      const response = await fetch(`/api/v1/moderation/queue?${params}`, {
        headers: {
          'X-Moderator-ID': moderatorId || '',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch queue');
      }

      const queue = await response.json();
      set({ queue, isLoadingQueue: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load queue',
        isLoadingQueue: false,
      });
    }
  },

  fetchQueueSummary: async () => {
    try {
      const response = await fetch('/api/v1/moderation/queue/summary');

      if (!response.ok) {
        throw new Error('Failed to fetch queue summary');
      }

      const summary = await response.json();
      set({ queueSummary: summary });
    } catch (error) {
      console.error('Failed to load queue summary:', error);
    }
  },

  // Review actions
  startReview: (report_id) => set({
    currentReview: {
      report_id,
      started_at: Date.now(),
      notes: '',
    },
  }),

  stopReview: () => set({
    currentReview: {
      report_id: null,
      started_at: null,
      notes: '',
    },
  }),

  updateNotes: (notes) => set((state) => ({
    currentReview: {
      ...state.currentReview,
      notes,
    },
  })),

  getReviewDuration: () => {
    const { currentReview } = get();
    if (!currentReview.started_at) return 0;
    return Math.floor((Date.now() - currentReview.started_at) / 1000);
  },

  // History actions
  setHistory: (history) => set({ history }),

  fetchHistory: async () => {
    set({ isLoadingHistory: true, error: null });

    try {
      const moderatorId = localStorage.getItem('moderator_id');
      const response = await fetch('/api/v1/moderation/history', {
        headers: {
          'X-Moderator-ID': moderatorId || '',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch history');
      }

      const history = await response.json();
      set({ history, isLoadingHistory: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load history',
        isLoadingHistory: false,
      });
    }
  },

  // Stats actions
  setStats: (stats) => set({ stats }),

  fetchStats: async (period_days = 30) => {
    set({ isLoadingStats: true, error: null });

    try {
      const moderatorId = localStorage.getItem('moderator_id');
      const response = await fetch(`/api/v1/moderation/stats?period_days=${period_days}`, {
        headers: {
          'X-Moderator-ID': moderatorId || '',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch stats');
      }

      const stats = await response.json();
      set({ stats, isLoadingStats: false });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load stats',
        isLoadingStats: false,
      });
    }
  },

  // Filter actions
  setFilters: (filters) => set({ filters }),

  // Error actions
  setError: (error) => set({ error }),

  // Loading actions
  setLoadingQueue: (isLoadingQueue) => set({ isLoadingQueue }),
  setLoadingHistory: (isLoadingHistory) => set({ isLoadingHistory }),
  setLoadingStats: (isLoadingStats) => set({ isLoadingStats }),
}));

// Selectors
export const selectQueue = (state: ModerationState) => state.queue;
export const selectQueueSummary = (state: ModerationState) => state.queueSummary;
export const selectCurrentReview = (state: ModerationState) => state.currentReview;
export const selectHistory = (state: ModerationState) => state.history;
export const selectStats = (state: ModerationState) => state.stats;
export const selectFilters = (state: ModerationState) => state.filters;
export const selectError = (state: ModerationState) => state.error;
