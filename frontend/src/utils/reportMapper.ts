/**
 * C.O.V.E.R.T - API Response → Store Report Mapper
 *
 * The backend returns snake_case fields; the frontend store uses camelCase.
 * This mapper bridges the two so components never crash on undefined field access.
 */

import type { Report, ReportStatus, ReportVisibility, ReportCategory } from '@/stores/reportStore';

/** Raw shape returned by the backend API (snake_case) */
export interface ApiReport {
    id: string;
    cid?: string;
    ipfs_cid?: string;
    cid_hash?: string;
    commitment_hash?: string;
    tx_hash?: string;
    transaction_hash?: string;
    category?: string;
    encrypted_category?: string;
    title?: string;
    description?: string;
    status?: string;
    visibility?: string;
    size_bytes?: number;
    file_size?: number;
    verification_score?: number;
    risk_level?: string;
    submitted_at?: string;
    submission_timestamp?: string;
    created_at?: string;
    updated_at?: string;
    reviewed_at?: string;
    message?: string;
    review_decision?: string;
    final_label?: string;
}

const VALID_STATUSES = new Set<ReportStatus>([
    // v2 lifecycle statuses
    'pending_review', 'needs_evidence', 'rejected_by_reviewer',
    'pending_moderation', 'appealed', 'verified', 'rejected', 'archived',
    // Legacy statuses (backward compat)
    'pending', 'under_review', 'disputed',
]);

const VALID_VISIBILITIES = new Set<ReportVisibility>([
    'private', 'moderated', 'public',
]);

const VALID_CATEGORIES = new Set<ReportCategory>([
    'corruption', 'fraud', 'safety', 'environment', 'human_rights', 'other',
]);

function safeStatus(v: string | undefined): ReportStatus {
    if (v && VALID_STATUSES.has(v as ReportStatus)) return v as ReportStatus;
    return 'pending_review';
}

function safeVisibility(v: string | undefined): ReportVisibility {
    if (v && VALID_VISIBILITIES.has(v as ReportVisibility)) return v as ReportVisibility;
    return 'moderated';
}

function safeCategory(v: string | undefined): ReportCategory {
    if (v && VALID_CATEGORIES.has(v as ReportCategory)) return v as ReportCategory;
    return 'other';
}

/**
 * Convert one backend API report object → frontend `Report` store shape.
 * Handles both possible field name variants gracefully.
 */
export function mapApiReport(api: ApiReport): Report {
    return {
        id: api.id,
        // CID / IPFS
        ipfsCid: api.cid ?? api.ipfs_cid ?? '',
        // Commitment hash (keccak256 of CID)
        commitmentHash: api.cid_hash ?? api.commitment_hash ?? '',
        // Transaction hash
        transactionHash: api.tx_hash ?? api.transaction_hash ?? '',
        // Category — stored encrypted on chain; backend echoes back the label
        category: safeCategory(api.category ?? api.encrypted_category),
        title: api.title,
        description: api.description,
        status: safeStatus(api.status),
        visibility: safeVisibility(api.visibility),
        verificationScore: api.verification_score,
        riskLevel: api.risk_level as Report['riskLevel'],
        fileSize: api.size_bytes ?? api.file_size ?? 0,
        submittedAt:
            api.submitted_at ??
            api.submission_timestamp ??
            api.created_at ??
            new Date().toISOString(),
        updatedAt: api.updated_at,
        reviewDecisionLabel: api.review_decision,
        finalLabel: api.final_label,
    };
}

/** Map an array of API reports */
export function mapApiReports(apiReports: ApiReport[]): Report[] {
    return apiReports.map(mapApiReport);
}
