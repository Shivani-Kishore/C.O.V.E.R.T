import type { ZKProof } from './zkp';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export interface ZKPVerificationResponse {
  is_valid: boolean;
  commitment: string | null;
  nullifier_hash: string | null;
  error: string | null;
}

export interface RateLimitResponse {
  allowed: boolean;
  current_count: number;
  limit: number;
  reset_at: string;
}

export const zkpApi = {
  async verifyProof(proof: ZKProof, publicSignals: string[]): Promise<ZKPVerificationResponse> {
    const response = await fetch(`${API_BASE}/zkp/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        proof,
        public_signals: publicSignals,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Verification failed');
    }

    return await response.json();
  },

  async checkNullifierUniqueness(nullifier: string): Promise<boolean> {
    const response = await fetch(`${API_BASE}/zkp/check-nullifier`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ nullifier }),
    });

    if (!response.ok) {
      throw new Error('Failed to check nullifier');
    }

    const data = await response.json();
    return data.is_unique;
  },

  async checkRateLimit(nullifier: string): Promise<RateLimitResponse> {
    const response = await fetch(`${API_BASE}/zkp/rate-limit/${nullifier}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error('Failed to check rate limit');
    }

    return await response.json();
  },

  async submitNullifier(
    nullifier: string,
    commitment: string,
    reportId: string
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/zkp/submit-nullifier`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        nullifier,
        commitment,
        report_id: reportId,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to submit nullifier');
    }
  },

  async healthCheck(): Promise<{ status: string; verification_key_loaded: boolean; message: string }> {
    const response = await fetch(`${API_BASE}/zkp/health`, {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error('Health check failed');
    }

    return await response.json();
  },
};
