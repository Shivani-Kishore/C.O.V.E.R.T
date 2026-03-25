/**
 * C.O.V.E.R.T - Reviewer Dashboard (Full-Featured)
 *
 * Features (high → low priority):
 * HIGH:   Priority sort + filters, Eligibility status panel, Change decision,
 *         Reporter deep-dive chip, Rep threshold alert banner
 * MEDIUM: Decision reasoning notes, Performance stats card, Age color coding,
 *         Batch decisions, IPFS content hash viewer
 * LOW:    Review accuracy tracker, Streak counter, Community stats, Keyboard shortcuts
 */

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
    EyeIcon,
    CheckBadgeIcon,
    ShieldExclamationIcon,
    DocumentMagnifyingGlassIcon,
    ExclamationTriangleIcon,
    ClockIcon,
    ArrowPathIcon,
    ChevronDownIcon,
    UserCircleIcon,
    ClipboardDocumentIcon,
    XMarkIcon,
    FireIcon,
    ChartBarIcon,
    BoltIcon,
    CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { useWeb3 } from '@/hooks/useWeb3';
import { useRoleAccess } from '@/hooks/useRoleAccess';
import {
    FinalLabel,
    ReviewerDecision,
    FINAL_LABEL_NAMES,
    FINAL_LABEL_COLORS,
    REVIEWER_DECISION_NAMES,
    STAKES,
} from '@/types/protocol';
import toast from 'react-hot-toast';
import { protocolService } from '@/services/protocol';
import { useReviewDecisionStore } from '@/stores/reviewDecisionStore';
import { EvidenceViewer } from '@/components/EvidenceViewer';
import { API_BASE } from '@/config';

// ─────────── Types ───────────

interface ReviewableReport {
    id: number;
    reporter: string;
    visibility: 'PUBLIC' | 'PRIVATE';
    contentHash: string;
    finalLabel: FinalLabel;
    reviewDecision: ReviewerDecision;
    createdAt: number;
    supportCount: number;
    challengeCount: number;
    hasAppeal: boolean;
    stake: number;
}

interface EligibilityData {
    eligible: boolean;
    rep_ok: boolean;
    age_ok: boolean;
    slash_ok: boolean;
    strikes_ok: boolean;
    active_strikes: number;
    reputation_score?: number;
}

interface ActorRepData {
    wallet_address: string;
    reputation_score: number;
    tier: string;
    strikes: number;
    last_strike_at?: string;
    last_slash_at?: string;
    account_created_at?: string;
}

type TabKey = 'queue' | 'my-reviews' | 'accuracy' | 'community';
type SortKey = 'oldest' | 'newest' | 'most_supported' | 'most_challenged';
type FilterKey = 'unreviewed' | 'reviewed' | 'appealed' | 'finalized' | 'all';

// ─────────── Mock data (dev fallback) ───────────

const MOCK_REPORTS: ReviewableReport[] = [
    {
        id: 0,
        reporter: '0x1234567890abcdef1234567890abcdef12345678',
        visibility: 'PUBLIC',
        contentHash: '0xabc123def456789012345678901234567890123456789012345678901234567890',
        finalLabel: FinalLabel.UNREVIEWED,
        reviewDecision: ReviewerDecision.NONE,
        createdAt: Date.now() / 1000 - 3600 * 2,
        supportCount: 3,
        challengeCount: 1,
        hasAppeal: false,
        stake: STAKES.REPORT_PUBLIC,
    },
    {
        id: 1,
        reporter: '0x5678901234567890abcdef1234567890abcdef12',
        visibility: 'PUBLIC',
        contentHash: '0xdef456abc789012345678901234567890123456789012345678901234567890123',
        finalLabel: FinalLabel.UNREVIEWED,
        reviewDecision: ReviewerDecision.NONE,
        createdAt: Date.now() / 1000 - 3600 * 30,
        supportCount: 7,
        challengeCount: 0,
        hasAppeal: false,
        stake: STAKES.REPORT_PUBLIC,
    },
    {
        id: 2,
        reporter: '0x9abcdef1234567890abcdef1234567890abcdef12',
        visibility: 'PRIVATE',
        contentHash: '0x789abcdef0123456789012345678901234567890123456789012345678901234',
        finalLabel: FinalLabel.CORROBORATED,
        reviewDecision: ReviewerDecision.REVIEW_PASSED,
        createdAt: Date.now() / 1000 - 3600 * 80,
        supportCount: 1,
        challengeCount: 4,
        hasAppeal: true,
        stake: STAKES.REPORT_PRIVATE,
    },
];

// ─────────── Helpers ───────────

function formatTimeAgo(ts: number): string {
    const s = Math.floor(Date.now() / 1000 - ts);
    if (s < 60) return `${s}s ago`;
    const m = Math.floor(s / 60);
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    if (h < 24) return `${h}h ago`;
    return `${Math.floor(h / 24)}d ago`;
}

function truncAddr(addr: string): string {
    if (addr.length <= 13) return addr;
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`;
}

// Streak helpers (localStorage-backed)
const STREAK_KEY = (wallet: string) => `covert_review_streak_${wallet.toLowerCase()}`;

function getStreak(wallet: string): { count: number; lastDate: string } {
    try {
        const raw = localStorage.getItem(STREAK_KEY(wallet));
        if (raw) return JSON.parse(raw);
    } catch { /* ignore */ }
    return { count: 0, lastDate: '' };
}

function updateStreak(wallet: string): number {
    const today = new Date().toISOString().slice(0, 10);
    const data = getStreak(wallet);
    if (data.lastDate === today) return data.count;
    const yesterday = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
    const newCount = data.lastDate === yesterday ? data.count + 1 : 1;
    localStorage.setItem(STREAK_KEY(wallet), JSON.stringify({ count: newCount, lastDate: today }));
    return newCount;
}

// ─────────── Sub-components ───────────

function EligibilityPanel({
    eligibility,
    loading,
}: {
    eligibility: EligibilityData | null;
    loading: boolean;
}) {
    const [open, setOpen] = useState(false);

    if (loading) {
        return (
            <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-4 animate-pulse">
                <div className="h-5 bg-neutral-800 rounded w-1/3" />
            </div>
        );
    }
    if (!eligibility) return null;

    const checks = [
        { label: 'Rep ≥ 50', ok: eligibility.rep_ok, detail: `Score: ${eligibility.reputation_score ?? '—'}` },
        { label: 'Account ≥ 30 days', ok: eligibility.age_ok, detail: '' },
        { label: 'No slash in 30d', ok: eligibility.slash_ok, detail: '' },
        { label: 'Strikes < 3 (30d)', ok: eligibility.strikes_ok, detail: `Active: ${eligibility.active_strikes}` },
    ];

    return (
        <div className={`rounded-2xl border p-4 ${eligibility.eligible
            ? 'bg-neutral-950 border-green-900/50'
            : 'bg-neutral-950 border-red-900/50'
        }`}>
            <button onClick={() => setOpen(o => !o)} className="flex items-center justify-between w-full">
                <div className="flex items-center gap-2">
                    {eligibility.eligible
                        ? <CheckCircleIcon className="h-5 w-5 text-green-500" />
                        : <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
                    }
                    <span className={`font-medium text-sm ${eligibility.eligible ? 'text-green-400' : 'text-red-400'}`}>
                        {eligibility.eligible ? 'Reviewer Eligible' : 'Reviewer Ineligible'}
                    </span>
                </div>
                <ChevronDownIcon className={`h-4 w-4 transition-transform ${eligibility.eligible ? 'text-green-500' : 'text-red-500'} ${open ? 'rotate-180' : ''}`} />
            </button>

            {open && (
                <div className="mt-3 grid grid-cols-2 gap-2">
                    {checks.map(c => (
                        <div key={c.label} className="flex items-center gap-2 text-xs">
                            <span className={c.ok ? 'text-green-500' : 'text-red-500'}>{c.ok ? 'Yes' : 'No'}</span>
                            <span className={c.ok ? 'text-green-400' : 'text-red-400'}>
                                {c.label}{c.detail ? ` (${c.detail})` : ''}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function RepAlertBanner({ score }: { score: number | undefined }) {
    if (score === undefined || score > 70 || score < 50) return null;
    return (
        <div className="rounded-2xl border border-amber-900/50 bg-neutral-950 px-4 py-3 flex items-center gap-3">
            <ExclamationTriangleIcon className="h-5 w-5 text-amber-500 flex-shrink-0" />
            <div>
                <p className="text-sm font-medium text-amber-400">Rep Warning: {score} / 50 threshold</p>
                <p className="text-xs text-neutral-500">
                    Your reviewer badge deactivates if rep drops below 50. Incorrect reviews cost rep.
                </p>
            </div>
        </div>
    );
}

function ActorDeepDivePanel({
    wallet,
    onClose,
}: {
    wallet: string;
    onClose: () => void;
}) {
    const [data, setData] = useState<ActorRepData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        fetch(`${API_BASE}/api/v1/reputation/wallet/${wallet}`)
            .then(r => r.json())
            .then(d => { if (!cancelled) { setData(d); setLoading(false); } })
            .catch(() => { if (!cancelled) setLoading(false); });
        return () => { cancelled = true; };
    }, [wallet]);

    const TIER_COLORS: Record<string, string> = {
        tier_3: 'text-white bg-neutral-700',
        tier_2: 'text-neutral-200 bg-neutral-800',
        tier_1: 'text-neutral-400 bg-neutral-900',
        tier_0: 'text-neutral-400 bg-neutral-800',
    };

    return (
        <div className="fixed inset-0 z-50 flex justify-end" onClick={onClose}>
            <div
                className="w-80 bg-neutral-950 h-full shadow-xl border-l border-neutral-800 flex flex-col"
                onClick={e => e.stopPropagation()}
            >
                <div className="flex items-center justify-between p-4 border-b border-neutral-800">
                    <div className="flex items-center gap-2">
                        <UserCircleIcon className="h-5 w-5 text-neutral-400" />
                        <h3 className="font-semibold text-white">Reporter Profile</h3>
                    </div>
                    <button onClick={onClose}>
                        <XMarkIcon className="h-5 w-5 text-neutral-500 hover:text-white" />
                    </button>
                </div>

                <div className="p-4 flex-1 overflow-y-auto space-y-4">
                    <div>
                        <p className="text-xs text-neutral-500 mb-1">Wallet</p>
                        <div className="flex items-center gap-2">
                            <code className="text-xs font-mono text-neutral-400 break-all">{wallet}</code>
                            <button onClick={() => { navigator.clipboard.writeText(wallet); toast.success('Copied'); }} className="flex-shrink-0">
                                <ClipboardDocumentIcon className="h-4 w-4 text-neutral-500 hover:text-white" />
                            </button>
                        </div>
                    </div>

                    {loading ? (
                        <div className="space-y-3">
                            {[1, 2, 3, 4].map(i => <div key={i} className="animate-pulse h-16 bg-neutral-900 rounded" />)}
                        </div>
                    ) : data ? (
                        <div className="grid grid-cols-2 gap-3">
                            <div className="bg-neutral-900 rounded-lg p-3">
                                <p className="text-xs text-neutral-500">Rep Score</p>
                                <p className="text-2xl font-bold text-white">{data.reputation_score}</p>
                            </div>
                            <div className="bg-neutral-900 rounded-lg p-3">
                                <p className="text-xs text-neutral-500">Tier</p>
                                <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs font-medium ${TIER_COLORS[data.tier] ?? 'text-neutral-400 bg-neutral-800'}`}>
                                    {data.tier?.replace('tier_', 'Tier ') ?? '—'}
                                </span>
                            </div>
                            <div className="bg-neutral-900 rounded-lg p-3">
                                <p className="text-xs text-neutral-500">Active Strikes</p>
                                <p className={`text-xl font-bold ${data.strikes > 0 ? 'text-red-500' : 'text-white'}`}>{data.strikes}</p>
                            </div>
                            <div className="bg-neutral-900 rounded-lg p-3">
                                <p className="text-xs text-neutral-500">Last Slash</p>
                                <p className="text-xs text-neutral-400 mt-1">
                                    {data.last_slash_at ? new Date(data.last_slash_at).toLocaleDateString() : 'None'}
                                </p>
                            </div>
                            {data.account_created_at && (
                                <div className="bg-neutral-900 rounded-lg p-3 col-span-2">
                                    <p className="text-xs text-neutral-500">Account Created</p>
                                    <p className="text-xs text-neutral-400 mt-1">
                                        {new Date(data.account_created_at).toLocaleDateString()}
                                    </p>
                                </div>
                            )}
                        </div>
                    ) : (
                        <p className="text-sm text-neutral-500">No reputation data found.</p>
                    )}
                </div>
            </div>
        </div>
    );
}

function ReviewerNotesField({
    reportId,
    reviewerAddress,
}: {
    reportId: number;
    reviewerAddress: string;
}) {
    const [content, setContent] = useState('');
    const [saving, setSaving] = useState(false);
    const [loaded, setLoaded] = useState(false);
    const [saved, setSaved] = useState(false);
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        fetch(`${API_BASE}/api/v1/moderation/notes/${reportId}`)
            .then(r => r.json())
            .then((notes: Array<{ moderator_address: string; content: string }>) => {
                const mine = notes.find(n => n.moderator_address.toLowerCase() === reviewerAddress.toLowerCase());
                if (mine) setContent(mine.content);
                setLoaded(true);
            })
            .catch(() => setLoaded(true));
    }, [reportId, reviewerAddress]);

    const handleChange = (val: string) => {
        setContent(val);
        setSaved(false);
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(async () => {
            setSaving(true);
            try {
                await fetch(`${API_BASE}/api/v1/moderation/notes/${reportId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(reviewerAddress ? { 'X-Wallet-Address': reviewerAddress } : {}),
                    },
                    body: JSON.stringify({ moderator_address: reviewerAddress, content: val }),
                });
                setSaved(true);
            } catch { /* ignore */ } finally {
                setSaving(false);
            }
        }, 2000);
    };

    return (
        <div className="mt-2">
            <div className="flex items-center justify-between mb-1">
                <p className="text-xs text-neutral-500 uppercase tracking-wider">Your Review Notes</p>
                {saving && <span className="text-xs text-neutral-500 animate-pulse">Saving…</span>}
                {!saving && saved && <span className="text-xs text-green-500">Saved</span>}
            </div>
            <textarea
                value={content}
                onChange={e => handleChange(e.target.value)}
                placeholder={loaded ? 'Add private notes about this report…' : 'Loading…'}
                disabled={!loaded}
                rows={3}
                className="w-full text-sm text-neutral-300 bg-neutral-900 border border-neutral-800 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-neutral-600 resize-none disabled:opacity-50 placeholder-neutral-600"
            />
        </div>
    );
}

function StatCard({
    label,
    value,
    colorClass,
    icon,
}: {
    label: string;
    value: string | number;
    colorClass: string;
    icon: React.ReactNode;
}) {
    return (
        <div className={`rounded-2xl border border-neutral-800 bg-neutral-950 p-4 hover:border-neutral-600 transition-all duration-500 ${colorClass}`}>
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-xs text-neutral-500 font-medium">{label}</p>
                    <p className="text-2xl font-bold text-white mt-1">{value}</p>
                </div>
                <div>{icon}</div>
            </div>
        </div>
    );
}

// ─────────── ReportDetailsPanel ───────────

interface BackendReportMeta {
    cid?: string;
    category?: string;
    title?: string;
    description?: string;
    status?: string;
    size_bytes?: number;
    submitted_at?: string;
    visibility?: string;
}

const CATEGORY_LABELS: Record<string, string> = {
    corruption: 'Corruption',
    fraud: 'Fraud',
    safety: 'Safety Violation',
    environment: 'Environmental',
    human_rights: 'Human Rights',
    other: 'Other',
};

function ReportDetailsPanel({ report }: { report: ReviewableReport }) {
    const [meta, setMeta] = useState<BackendReportMeta | null>(null);
    const [metaLoading, setMetaLoading] = useState(true);
    const [supporters, setSupporters] = useState<string[]>([]);
    const [challengers, setChallengers] = useState<string[]>([]);
    const [loadingActors, setLoadingActors] = useState(true);

    useEffect(() => {
        let cancelled = false;
        setMetaLoading(true);

        // Fetch report metadata directly by contentHash — no reporter impersonation needed
        fetch(`${API_BASE}/api/v1/reports/by-hash/${report.contentHash}`)
            .then(r => r.ok ? r.json() : null)
            .then(data => {
                if (cancelled) return;
                setMeta(data ?? null);
                setMetaLoading(false);
            })
            .catch(() => { setMetaLoading(false); });

        // Fetch on-chain supporters and challengers
        setLoadingActors(true);
        Promise.all([
            protocolService.getSupporters(report.id).catch(() => [] as string[]),
            protocolService.getChallengers(report.id).catch(() => [] as string[]),
        ]).then(([sups, chals]) => {
            if (cancelled) return;
            setSupporters(sups);
            setChallengers(chals);
            setLoadingActors(false);
        });

        return () => { cancelled = true; };
    }, [report.id, report.contentHash]);

    return (
        <div className="space-y-5 mt-4">
            {/* Report content: title + description */}
            {metaLoading ? (
                <div className="animate-pulse space-y-3">
                    <div className="h-5 bg-neutral-800 rounded w-2/3" />
                    <div className="h-24 bg-neutral-800 rounded" />
                </div>
            ) : meta ? (
                <div className="space-y-4">
                    {/* Title */}
                    {meta.title && (
                        <div>
                            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Title</p>
                            <p className="text-base font-semibold text-white leading-snug">{meta.title}</p>
                        </div>
                    )}

                    {/* Description */}
                    {meta.description && (
                        <div>
                            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Description</p>
                            <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-4 max-h-60 overflow-y-auto">
                                <p className="text-sm text-neutral-200 whitespace-pre-wrap leading-relaxed">{meta.description}</p>
                            </div>
                        </div>
                    )}

                    {/* Metadata row */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                        {meta.category && (
                            <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3">
                                <p className="text-xs text-neutral-500 mb-1">Category</p>
                                <p className="text-sm font-medium text-white">{CATEGORY_LABELS[meta.category] ?? meta.category}</p>
                            </div>
                        )}
                        {meta.size_bytes != null && (
                            <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3">
                                <p className="text-xs text-neutral-500 mb-1">Evidence Size</p>
                                <p className="text-sm font-medium text-white">
                                    {meta.size_bytes < 1024 * 1024
                                        ? `${(meta.size_bytes / 1024).toFixed(1)} KB`
                                        : `${(meta.size_bytes / (1024 * 1024)).toFixed(1)} MB`}
                                </p>
                            </div>
                        )}
                        {meta.submitted_at && (
                            <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3">
                                <p className="text-xs text-neutral-500 mb-1">Submitted</p>
                                <p className="text-sm font-medium text-white">{new Date(meta.submitted_at).toLocaleDateString()}</p>
                            </div>
                        )}
                    </div>

                    {/* IPFS CID */}
                    {meta.cid && (
                        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3">
                            <p className="text-xs text-neutral-500 mb-1">IPFS CID (Encrypted Evidence Files)</p>
                            <div className="flex items-center gap-2">
                                <code className="text-xs font-mono text-neutral-400 truncate flex-1">{meta.cid}</code>
                                <button onClick={() => { navigator.clipboard.writeText(meta.cid!); toast.success('CID copied'); }}>
                                    <ClipboardDocumentIcon className="h-4 w-4 text-neutral-500 hover:text-white flex-shrink-0" />
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Evidence files — fetches AES key from backend and decrypts in-browser */}
                    {meta.cid && (
                        <EvidenceViewer
                            contentHash={report.contentHash}
                            cid={meta.cid}
                            visibility={meta.visibility ?? 'private'}
                        />
                    )}
                </div>
            ) : (
                <div className="text-center py-6 text-neutral-500 text-sm">
                    Report content not available — may have been submitted before this feature was enabled.
                </div>
            )}

            {/* Supporters & Challengers */}
            <div>
                <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">Community Interactions</p>
                {loadingActors ? (
                    <div className="animate-pulse grid grid-cols-2 gap-2">
                        <div className="h-20 bg-neutral-800 rounded-lg" />
                        <div className="h-20 bg-neutral-800 rounded-lg" />
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3">
                            <p className="text-xs font-medium text-neutral-300 mb-2">
                                Supporters ({supporters.length})
                            </p>
                            {supporters.length === 0 ? (
                                <p className="text-xs text-neutral-600">No supporters yet</p>
                            ) : (
                                <div className="space-y-1 max-h-28 overflow-y-auto">
                                    {supporters.map((addr, i) => (
                                        <p key={i} className="text-xs font-mono text-neutral-400">{addr}</p>
                                    ))}
                                </div>
                            )}
                        </div>
                        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-3">
                            <p className="text-xs font-medium text-neutral-400 mb-2">
                                Challengers ({challengers.length})
                            </p>
                            {challengers.length === 0 ? (
                                <p className="text-xs text-neutral-600">No challengers yet</p>
                            ) : (
                                <div className="space-y-1 max-h-28 overflow-y-auto">
                                    {challengers.map((addr, i) => (
                                        <p key={i} className="text-xs font-mono text-neutral-400">{addr}</p>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// ─────────── ReportCard ───────────

interface ReportCardProps {
    report: ReviewableReport;
    selected: boolean;
    reviewing: boolean;
    batchChecked: boolean;
    walletAddress: string;
    onToggle: () => void;
    onDecision: (id: number, decision: ReviewerDecision) => void;
    onViewActor: () => void;
    onBatchToggle: () => void;
}

function ReportCard({
    report,
    selected,
    reviewing,
    batchChecked,
    walletAddress,
    onToggle,
    onDecision,
    onViewActor,
    onBatchToggle,
}: ReportCardProps) {
    const hourAge = (Date.now() / 1000 - report.createdAt) / 3600;
    const ageCls = hourAge < 24 ? 'text-neutral-400' : hourAge < 72 ? 'text-neutral-300' : 'text-white';
    const ageLbl = hourAge < 24 ? 'Fresh' : hourAge < 72 ? 'Aging' : 'Overdue';

    return (
        <div
            className={`rounded-2xl border transition-all overflow-hidden ${selected
                ? 'border-neutral-600 shadow-[0_0_30px_rgba(255,255,255,0.03)] bg-neutral-950'
                : 'border-neutral-800 bg-neutral-950 hover:border-neutral-600'
                }`}
        >
            {/* Header row */}
            <div className="flex items-center">
                {/* Batch checkbox */}
                <div className="pl-4 py-4" onClick={e => e.stopPropagation()}>
                    <input
                        type="checkbox"
                        checked={batchChecked}
                        onChange={onBatchToggle}
                        className="h-4 w-4 rounded border-neutral-700 bg-neutral-900 text-white focus:ring-neutral-600"
                    />
                </div>

                <button onClick={onToggle} className="flex-1 px-4 py-4 text-left">
                    <div className="flex items-center justify-between gap-4">
                        <div className="flex flex-col gap-1.5 min-w-0">
                            <div className="flex items-center flex-wrap gap-2">
                                <span className="text-sm font-bold text-white">Report #{report.id}</span>
                                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-neutral-800 text-neutral-400">
                                    {report.visibility}
                                </span>
                                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${FINAL_LABEL_COLORS[report.finalLabel]}`}>
                                    {FINAL_LABEL_NAMES[report.finalLabel]}
                                </span>
                                {report.reviewDecision !== ReviewerDecision.NONE && (
                                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-neutral-800 text-neutral-300">
                                        {REVIEWER_DECISION_NAMES[report.reviewDecision]}
                                    </span>
                                )}
                                {report.hasAppeal && (
                                    <span className="px-2 py-0.5 rounded-full text-xs font-medium text-white" style={{ backgroundColor: '#E84B1A33', border: '1px solid #E84B1A66' }}>
                                        Appeal
                                    </span>
                                )}
                                <span className={`text-xs font-medium ${ageCls}`}>{ageLbl}</span>
                            </div>
                            <div className="flex items-center gap-3 text-xs text-neutral-500">
                                <span className={ageCls}>{formatTimeAgo(report.createdAt)}</span>
                                <span>·</span>
                                <span>By {truncAddr(report.reporter)}</span>
                                <span>·</span>
                                <span>Stake: {report.stake} COV</span>
                            </div>
                        </div>

                        <div className="flex items-center gap-4 flex-shrink-0">
                            <div className="flex items-center gap-3 text-sm">
                                <span className="flex items-center gap-1 text-neutral-300">
                                    <span className="font-semibold">{report.supportCount}</span>
                                    <span className="text-xs text-neutral-500">supports</span>
                                </span>
                                <span className="flex items-center gap-1 text-red-500">
                                    <span className="font-semibold">{report.challengeCount}</span>
                                    <span className="text-xs">challenges</span>
                                </span>
                            </div>
                            <ChevronDownIcon className={`h-5 w-5 text-neutral-500 transition-transform ${selected ? 'rotate-180' : ''}`} />
                        </div>
                    </div>
                </button>
            </div>

            {/* Expanded panel */}
            {selected && (
                <div className="border-t border-neutral-800 bg-neutral-900/50 p-5 space-y-5">
                    {/* Reporter + Content Hash row */}
                    <div className="flex flex-wrap gap-5">
                        <div>
                            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Reporter</p>
                            <button
                                onClick={onViewActor}
                                className="flex items-center gap-2 px-3 py-1.5 bg-neutral-900 border border-neutral-700 rounded-lg text-sm text-neutral-300 hover:border-neutral-500 hover:text-white transition-colors"
                            >
                                <UserCircleIcon className="h-4 w-4" />
                                {truncAddr(report.reporter)}
                                <span className="text-xs text-neutral-500">→ Profile</span>
                            </button>
                        </div>

                        <div className="flex-1 min-w-0">
                            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Content Hash</p>
                            <div className="flex items-center gap-2">
                                <code className="text-xs font-mono text-neutral-400 bg-neutral-900 px-2 py-1 rounded border border-neutral-800 truncate max-w-xs">
                                    {report.contentHash}
                                </code>
                                <button
                                    onClick={() => { navigator.clipboard.writeText(report.contentHash); toast.success('Hash copied'); }}
                                    title="Copy content hash"
                                >
                                    <ClipboardDocumentIcon className="h-4 w-4 text-neutral-500 hover:text-white" />
                                </button>
                            </div>
                            <p className="text-xs text-neutral-600 mt-1">
                                keccak256 of IPFS CID — use this hash to verify content integrity off-chain.
                            </p>
                        </div>

                        <div>
                            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-1">Appeal</p>
                            <p className="text-sm">
                                {report.hasAppeal
                                    ? <span className="font-medium" style={{ color: '#E84B1A' }}>Has Appeal</span>
                                    : <span className="text-neutral-600">None</span>
                                }
                            </p>
                        </div>
                    </div>

                    {/* Report content, IPFS, supporters, challengers */}
                    <ReportDetailsPanel report={report} />

                    {/* Decision buttons — always shown (change decision supported) */}
                    <div>
                        <p className="text-sm font-medium text-neutral-300 mb-2">
                            {report.reviewDecision !== ReviewerDecision.NONE
                                ? 'Change your decision:'
                                : 'Set your review decision:'}
                        </p>
                        <div className="flex flex-wrap gap-2">
                            <button
                                onClick={() => onDecision(report.id, ReviewerDecision.REVIEW_PASSED)}
                                disabled={reviewing}
                                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all disabled:opacity-50
                                    ${report.reviewDecision === ReviewerDecision.REVIEW_PASSED
                                        ? 'bg-orange-700 text-white ring-2 ring-orange-600'
                                        : 'bg-neutral-800 hover:bg-neutral-700 text-neutral-300 border border-neutral-700'
                                    }`}
                            >
                                {reviewing ? <ArrowPathIcon className="h-4 w-4 animate-spin" /> : <CheckBadgeIcon className="h-4 w-4" />}
                                Review Passed
                                <kbd className="ml-1 text-xs bg-neutral-700 px-1 rounded">P</kbd>
                            </button>
                            <button
                                onClick={() => onDecision(report.id, ReviewerDecision.NEEDS_EVIDENCE)}
                                disabled={reviewing}
                                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all disabled:opacity-50
                                    ${report.reviewDecision === ReviewerDecision.NEEDS_EVIDENCE
                                        ? 'bg-orange-700 text-white ring-2 ring-orange-600'
                                        : 'bg-neutral-800 hover:bg-neutral-700 text-neutral-300 border border-neutral-700'
                                    }`}
                            >
                                <ExclamationTriangleIcon className="h-4 w-4" />
                                Needs Evidence
                                <kbd className="ml-1 text-xs bg-neutral-700 px-1 rounded">N</kbd>
                            </button>
                            <button
                                onClick={() => onDecision(report.id, ReviewerDecision.REJECT_SPAM)}
                                disabled={reviewing}
                                className={`flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all disabled:opacity-50
                                    ${report.reviewDecision === ReviewerDecision.REJECT_SPAM
                                        ? 'bg-orange-700 text-white ring-2 ring-orange-600'
                                        : 'bg-neutral-800 hover:bg-neutral-700 text-neutral-300 border border-neutral-700'
                                    }`}
                            >
                                <ShieldExclamationIcon className="h-4 w-4" />
                                Reject Spam
                                <kbd className="ml-1 text-xs bg-neutral-700 px-1 rounded">R</kbd>
                            </button>
                        </div>
                    </div>

                    {/* Notes */}
                    <ReviewerNotesField reportId={report.id} reviewerAddress={walletAddress} />
                </div>
            )}
        </div>
    );
}

// ─────────── Main Component ───────────

export function ReviewerDashboard() {
    const { walletState } = useWeb3();
    const isConnected = walletState.connected;
    const walletAddress = walletState.address ?? '';
    const { covBalance, reputationScore } = useRoleAccess();

    // ── Core state ──
    const [tab, setTab] = useState<TabKey>('queue');
    const [sortKey, setSortKey] = useState<SortKey>('oldest');
    const [filter, setFilter] = useState<FilterKey>('unreviewed');
    const [reports, setReports] = useState<ReviewableReport[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedReport, setSelectedReport] = useState<ReviewableReport | null>(null);
    const [reviewingId, setReviewingId] = useState<number | null>(null);
    // Mutable ref so stale keyboard-shortcut closures can still see the live value.
    const reviewingRef = useRef<number | null>(null);
    // True only when reports came from CovertProtocol on-chain; false for DB/mock fallback.
    // On-chain actions (setReviewDecision) are blocked when false to prevent
    // calling the contract with fake sequential IDs from the DB fallback.
    const [fromBlockchain, setFromBlockchain] = useState(false);

    // ── Eligibility ──
    const [eligibility, setEligibility] = useState<EligibilityData | null>(null);
    const [eligibilityLoading, setEligibilityLoading] = useState(false);

    // ── Actor slide-over ──
    const [actorSlideOver, setActorSlideOver] = useState<string | null>(null);

    // ── Batch ──
    const [batchSelected, setBatchSelected] = useState<Set<number>>(new Set());
    const [batchDecision, setBatchDecision] = useState<ReviewerDecision>(ReviewerDecision.REJECT_SPAM);
    const [batchSubmitting, setBatchSubmitting] = useState(false);

    // ── Streak ──
    const [streak, setStreak] = useState(0);
    useEffect(() => {
        if (walletAddress) setStreak(getStreak(walletAddress).count);
    }, [walletAddress]);

    // ── Eligibility fetch ──
    const fetchEligibility = useCallback(async () => {
        if (!walletAddress) return;
        setEligibilityLoading(true);
        try {
            const [r1, r2] = await Promise.all([
                fetch(`${API_BASE}/api/v1/reputation/reviewer-eligibility/${walletAddress}`),
                fetch(`${API_BASE}/api/v1/reputation/wallet/${walletAddress}`),
            ]);
            const [d1, d2] = await Promise.all([r1.json(), r2.json()]);
            setEligibility({ ...d1, reputation_score: d2.reputation_score ?? 0 });
        } catch { /* silently ignore */ } finally {
            setEligibilityLoading(false);
        }
    }, [walletAddress]);

    // ── Reports fetch ──
    const fetchReports = useCallback(async () => {
        if (!isConnected) return;
        setLoading(true);
        try {
            let usedBlockchain = false;

            // Try blockchain first
            try {
                await protocolService.connect();
                const count = await protocolService.getReportCount();
                const rawReports = await protocolService.getReportsInRange(0, count);

                if (rawReports.length > 0) {
                    const enriched = await Promise.all(rawReports.map(async (r) => {
                        const [support, challenge] = await Promise.all([
                            protocolService.getSupporterCount(r.id),
                            protocolService.getChallengerCount(r.id),
                        ]);
                        return {
                            ...r,
                            visibility: r.visibility === 0 ? 'PUBLIC' : 'PRIVATE' as 'PUBLIC' | 'PRIVATE',
                            supportCount: support,
                            challengeCount: challenge,
                            stake: r.visibility === 0 ? STAKES.REPORT_PUBLIC : STAKES.REPORT_PRIVATE,
                        } as ReviewableReport;
                    }));
                    setReports(enriched);
                    setFromBlockchain(true);
                    usedBlockchain = true;
                }
            } catch {
                // Blockchain unavailable — fall through to DB fetch
            }

            if (!usedBlockchain) {
                setFromBlockchain(false);
                // Fall back to backend DB — shows all reports from all wallets
                const res = await fetch(`${API_BASE}/api/v1/reports/all?limit=100`, {
                    headers: {
                        ...(walletAddress ? { 'X-Wallet-Address': walletAddress } : {}),
                    },
                });
                if (res.ok) {
                    const data = await res.json();
                    const DB_REVIEW_DECISION: Record<string, ReviewerDecision> = {
                        'REVIEW_PASSED': ReviewerDecision.REVIEW_PASSED,
                        'NEEDS_EVIDENCE': ReviewerDecision.NEEDS_EVIDENCE,
                        'REJECT_SPAM': ReviewerDecision.REJECT_SPAM,
                    };
                    // Infer reviewDecision from DB status when review_decision field is absent
                    const STATUS_TO_REVIEW_DECISION: Record<string, ReviewerDecision> = {
                        'pending_review': ReviewerDecision.NONE,
                        'pending': ReviewerDecision.NONE,
                        'needs_evidence': ReviewerDecision.NEEDS_EVIDENCE,
                        'rejected_by_reviewer': ReviewerDecision.REJECT_SPAM,
                        'pending_moderation': ReviewerDecision.REVIEW_PASSED,
                        'appealed': ReviewerDecision.REVIEW_PASSED,
                        'verified': ReviewerDecision.REVIEW_PASSED,
                        'rejected': ReviewerDecision.REVIEW_PASSED,
                    };
                    const STATUS_TO_FINAL_LABEL: Record<string, FinalLabel> = {
                        'verified': FinalLabel.CORROBORATED,
                        'rejected': FinalLabel.FALSE_OR_MANIPULATED,
                        'disputed': FinalLabel.DISPUTED,
                    };
                    const dbReports: ReviewableReport[] = (data.items || []).map(
                        (r: { reporter?: string; visibility: string; cid_hash?: string; submitted_at?: string; review_decision?: string; status?: string }, idx: number) => ({
                            id: idx + 1,
                            reporter: r.reporter || '0x0000000000000000000000000000000000000000',
                            visibility: r.visibility === 'public' ? 'PUBLIC' : 'PRIVATE' as 'PUBLIC' | 'PRIVATE',
                            contentHash: r.cid_hash || '',
                            finalLabel: (r.status && STATUS_TO_FINAL_LABEL[r.status]) ?? FinalLabel.UNREVIEWED,
                            reviewDecision: (r.review_decision && DB_REVIEW_DECISION[r.review_decision])
                                ?? (r.status && STATUS_TO_REVIEW_DECISION[r.status])
                                ?? ReviewerDecision.NONE,
                            createdAt: r.submitted_at ? new Date(r.submitted_at).getTime() / 1000 : Date.now() / 1000,
                            supportCount: 0,
                            challengeCount: 0,
                            hasAppeal: r.status === 'appealed',
                            stake: r.visibility === 'public' ? STAKES.REPORT_PUBLIC : STAKES.REPORT_PRIVATE,
                        })
                    );
                    setReports(dbReports);
                } else if (import.meta.env.VITE_DEV_MODE === 'true') {
                    setReports(MOCK_REPORTS);
                } else {
                    toast.error('Failed to load reports');
                }
            }
        } catch (err) {
            console.error(err);
            setFromBlockchain(false);
            if (import.meta.env.VITE_DEV_MODE === 'true') {
                setReports(MOCK_REPORTS);
            } else {
                toast.error('Failed to load reports from blockchain');
            }
        } finally {
            setLoading(false);
        }
    }, [isConnected]);

    useEffect(() => {
        if (isConnected) {
            fetchReports();
            fetchEligibility();
        } else {
            setReports([]);
            setEligibility(null);
        }
    }, [isConnected, fetchReports, fetchEligibility]);

    // Re-fetch when another dashboard dispatches a decision/finalization event
    useEffect(() => {
        window.addEventListener('covert:reports-updated', fetchReports);
        return () => window.removeEventListener('covert:reports-updated', fetchReports);
    }, [fetchReports]);

    // ── Decision handler ──
    const handleSetDecision = async (reportId: number, decision: ReviewerDecision) => {
        if (reviewingRef.current !== null) return; // guard against keyboard-repeat or double-click
        reviewingRef.current = reportId;
        setReviewingId(reportId);
        try {
            // On-chain decision only when reports come from the blockchain
            if (fromBlockchain) {
                await protocolService.connect();
                await protocolService.setReviewDecision(reportId, decision);
            }

            // Track vote locally so partial stake return triggers correctly
            useReviewDecisionStore.getState().recordDecision(String(reportId), ReviewerDecision[decision] as 'REVIEW_PASSED' | 'NEEDS_EVIDENCE' | 'REJECT_SPAM');

            // Update local state
            setReports(prev => prev.map(r => r.id === reportId ? { ...r, reviewDecision: decision } : r));
            if (selectedReport?.id === reportId) {
                setSelectedReport(prev => prev ? { ...prev, reviewDecision: decision } : null);
            }

            // Sync status + decision to backend DB so moderator/reporter dashboards update
            // Map reviewer decision → new lifecycle status:
            //   REVIEW_PASSED  → pending_moderation  (goes to moderator queue)
            //   NEEDS_EVIDENCE → needs_evidence       (returned to reporter)
            //   REJECT_SPAM    → rejected_by_reviewer (returned to reporter)
            const DECISION_TO_STATUS: Record<number, string> = {
                [ReviewerDecision.REVIEW_PASSED]:  'pending_moderation',
                [ReviewerDecision.NEEDS_EVIDENCE]: 'needs_evidence',
                [ReviewerDecision.REJECT_SPAM]:    'rejected_by_reviewer',
            };
            const targetReport = reports.find(r => r.id === reportId);
            if (targetReport?.contentHash) {
                fetch(`${API_BASE}/api/v1/reports/by-hash/${targetReport.contentHash}/status`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        ...(walletAddress ? { 'X-Wallet-Address': walletAddress } : {}),
                    },
                    body: JSON.stringify({
                        status: DECISION_TO_STATUS[decision] ?? 'pending_moderation',
                        reviewer_address: walletAddress,
                        review_decision: ReviewerDecision[decision],
                    }),
                }).catch(() => { /* non-critical */ });
            }

            const newStreak = updateStreak(walletAddress);
            setStreak(newStreak);
            const msg = `Decision set: ${REVIEWER_DECISION_NAMES[decision]}`;
            toast.success(newStreak > 1 ? `${msg} — ${newStreak}-day streak!` : msg);
            window.dispatchEvent(new CustomEvent('covert:reports-updated'));
        } catch (err) {
            const raw = err instanceof Error ? err.message : String(err);
            const missingRole = raw.toLowerCase().includes('missing role')
                || raw.toLowerCase().includes('accesscontrol')
                || raw.toLowerCase().includes('not have role');
            if (missingRole) {
                toast.error('Your wallet does not have REVIEWER_ROLE. Contact the protocol administrator to grant reviewer access to your wallet.');
            } else if (raw.toLowerCase().includes('user rejected') || raw.toLowerCase().includes('user denied')) {
                toast.error('Transaction rejected');
            } else {
                toast.error(`Failed to set review decision: ${raw.slice(0, 120)}`);
            }
            console.error(err);
        } finally {
            reviewingRef.current = null;
            setReviewingId(null);
        }
    };

    // ── Keyboard shortcuts ──
    useEffect(() => {
        if (!selectedReport) return;
        const reportId = selectedReport.id;
        const handler = (e: KeyboardEvent) => {
            if (e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLInputElement) return;
            if (e.key === 'p' || e.key === 'P') handleSetDecision(reportId, ReviewerDecision.REVIEW_PASSED);
            if (e.key === 'n' || e.key === 'N') handleSetDecision(reportId, ReviewerDecision.NEEDS_EVIDENCE);
            if (e.key === 'r' || e.key === 'R') handleSetDecision(reportId, ReviewerDecision.REJECT_SPAM);
            if (e.key === 'Escape') setSelectedReport(null);
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [selectedReport]); // eslint-disable-line react-hooks/exhaustive-deps

    // ── Batch submit ──
    const handleBatchSubmit = async () => {
        if (batchSelected.size === 0) return;
        setBatchSubmitting(true);
        let done = 0;
        if (fromBlockchain) {
            await protocolService.connect();
        }
        for (const id of batchSelected) {
            try {
                if (fromBlockchain) {
                    await protocolService.setReviewDecision(id, batchDecision);
                }
                useReviewDecisionStore.getState().recordDecision(String(id), ReviewerDecision[batchDecision] as 'REVIEW_PASSED' | 'NEEDS_EVIDENCE' | 'REJECT_SPAM');
                setReports(prev => prev.map(r => r.id === id ? { ...r, reviewDecision: batchDecision } : r));
                // Sync status + decision to backend
                const DECISION_TO_STATUS_BATCH: Record<number, string> = {
                    [ReviewerDecision.REVIEW_PASSED]:  'pending_moderation',
                    [ReviewerDecision.NEEDS_EVIDENCE]: 'needs_evidence',
                    [ReviewerDecision.REJECT_SPAM]:    'rejected_by_reviewer',
                };
                const target = reports.find(r => r.id === id);
                if (target?.contentHash) {
                    fetch(`${API_BASE}/api/v1/reports/by-hash/${target.contentHash}/status`, {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json',
                            ...(walletAddress ? { 'X-Wallet-Address': walletAddress } : {}),
                        },
                        body: JSON.stringify({
                            status: DECISION_TO_STATUS_BATCH[batchDecision] ?? 'pending_moderation',
                            reviewer_address: walletAddress,
                            review_decision: ReviewerDecision[batchDecision],
                        }),
                    }).catch(() => {});
                }
                done++;
            } catch {
                toast.error(`Failed on report #${id}`);
            }
        }
        setBatchSelected(new Set());
        setBatchSubmitting(false);
        toast.success(`Submitted ${done} decision(s): ${REVIEWER_DECISION_NAMES[batchDecision]}`);
        window.dispatchEvent(new CustomEvent('covert:reports-updated'));
    };

    // ── Filtering & sorting ──
    const filteredReports = useMemo(() => {
        return reports.filter(r => {
            // Exclude own reports — reviewers cannot review their own submissions
            if (walletAddress && r.reporter.toLowerCase() === walletAddress.toLowerCase()) return false;
            if (filter === 'unreviewed') return r.reviewDecision === ReviewerDecision.NONE && r.finalLabel === FinalLabel.UNREVIEWED;
            if (filter === 'reviewed') return r.reviewDecision !== ReviewerDecision.NONE;
            if (filter === 'appealed') return r.hasAppeal;
            if (filter === 'finalized') return r.finalLabel !== FinalLabel.UNREVIEWED;
            return true;
        });
    }, [reports, filter, walletAddress]);

    const sortedReports = useMemo(() => {
        const arr = [...filteredReports];
        if (sortKey === 'oldest') return arr.sort((a, b) => a.createdAt - b.createdAt);
        if (sortKey === 'newest') return arr.sort((a, b) => b.createdAt - a.createdAt);
        if (sortKey === 'most_supported') return arr.sort((a, b) => b.supportCount - a.supportCount);
        if (sortKey === 'most_challenged') return arr.sort((a, b) => b.challengeCount - a.challengeCount);
        return arr;
    }, [filteredReports, sortKey]);

    // ── Derived stats ──
    const totalReviewed = useMemo(() => reports.filter(r => r.reviewDecision !== ReviewerDecision.NONE).length, [reports]);
    const totalUnreviewed = useMemo(() => reports.filter(r => r.reviewDecision === ReviewerDecision.NONE && r.finalLabel === FinalLabel.UNREVIEWED).length, [reports]);
    const totalAppealed = useMemo(() => reports.filter(r => r.hasAppeal).length, [reports]);

    const decisionBreakdown = useMemo(() => ({
        passed: reports.filter(r => r.reviewDecision === ReviewerDecision.REVIEW_PASSED).length,
        needsEvidence: reports.filter(r => r.reviewDecision === ReviewerDecision.NEEDS_EVIDENCE).length,
        rejected: reports.filter(r => r.reviewDecision === ReviewerDecision.REJECT_SPAM).length,
    }), [reports]);

    const accuracyStats = useMemo(() => {
        const finalized = reports.filter(r =>
            r.finalLabel !== FinalLabel.UNREVIEWED && r.reviewDecision !== ReviewerDecision.NONE
        );
        const correct = finalized.filter(r => {
            if (r.finalLabel === FinalLabel.CORROBORATED) return r.reviewDecision === ReviewerDecision.REVIEW_PASSED;
            if (r.finalLabel === FinalLabel.FALSE_OR_MANIPULATED) return r.reviewDecision === ReviewerDecision.REJECT_SPAM;
            if (r.finalLabel === FinalLabel.NEEDS_EVIDENCE || r.finalLabel === FinalLabel.DISPUTED) return r.reviewDecision === ReviewerDecision.NEEDS_EVIDENCE;
            return false;
        });
        return {
            total: finalized.length,
            correct: correct.length,
            pct: finalized.length ? Math.round(100 * correct.length / finalized.length) : 0,
        };
    }, [reports]);

    const communityStats = useMemo(() => {
        const n = reports.length;
        return {
            avgSupport: n ? (reports.reduce((s, r) => s + r.supportCount, 0) / n).toFixed(1) : '0',
            avgChallenge: n ? (reports.reduce((s, r) => s + r.challengeCount, 0) / n).toFixed(1) : '0',
            appealsRate: n ? Math.round(100 * reports.filter(r => r.hasAppeal).length / n) : 0,
            labelDist: Object.values(FinalLabel)
                .filter(v => typeof v === 'number')
                .map(v => ({
                    label: v as FinalLabel,
                    count: reports.filter(r => r.finalLabel === v).length,
                    pct: n ? Math.round(100 * reports.filter(r => r.finalLabel === v).length / n) : 0,
                })),
        };
    }, [reports]);

    // ─────────── Not connected ───────────
    if (!isConnected) {
        return (
            <div className="flex flex-col items-center justify-center py-20 text-center">
                <ShieldExclamationIcon className="h-16 w-16 text-neutral-700 mb-4" />
                <h2 className="text-xl font-semibold text-white mb-2">Connect Your Wallet</h2>
                <p className="text-neutral-500 max-w-md">
                    Connect your wallet to access the Reviewer Dashboard. You must hold an active Reviewer Badge.
                </p>
            </div>
        );
    }

    // ─────────── Render ───────────
    return (
        <div className="space-y-5 pb-24">
            {/* Action bar */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    {streak > 0 && (
                        <div className="flex items-center gap-1 border border-neutral-700 rounded-lg px-3 py-2">
                            <FireIcon className="h-4 w-4 text-orange-500" />
                            <span className="text-sm font-bold text-white">{streak}d streak</span>
                        </div>
                    )}
                </div>
                <div className="flex items-center gap-2">
                    {/* Rep warning tooltip (replaces banner) */}
                    {eligibility?.reputation_score !== undefined && eligibility.reputation_score >= 50 && eligibility.reputation_score <= 70 && (
                        <div className="relative group">
                            <button className="w-7 h-7 rounded-full border border-neutral-700 text-neutral-400 text-xs flex items-center justify-center hover:border-neutral-500 hover:text-white transition-colors">
                                ⓘ
                            </button>
                            <div className="absolute right-0 top-9 z-20 w-64 bg-neutral-900 border border-neutral-700 rounded-xl p-3 text-xs text-neutral-400 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity shadow-2xl">
                                <p className="font-semibold mb-1" style={{ color: '#E84B1A' }}>Rep Warning — {eligibility.reputation_score} / 50</p>
                                <p>Your reviewer badge deactivates if rep drops below 50. Incorrect decisions cost rep.</p>
                            </div>
                        </div>
                    )}
                    <button
                        onClick={() => { fetchReports(); fetchEligibility(); }}
                        className="flex items-center gap-2 px-4 py-2 border border-neutral-700 hover:border-neutral-500 rounded-lg text-sm font-medium text-neutral-300 hover:text-white transition-colors"
                    >
                        <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-3 gap-3">
                <StatCard label="Pending" value={totalUnreviewed} colorClass="" icon={<ClockIcon className="h-5 w-5 text-neutral-400" />} />
                <StatCard label="Reviewed" value={totalReviewed} colorClass="" icon={<CheckBadgeIcon className="h-5 w-5 text-neutral-400" />} />
                <StatCard label="Appealed" value={totalAppealed} colorClass="" icon={<ExclamationTriangleIcon className="h-5 w-5 text-neutral-400" />} />
            </div>

            {/* Two-column layout: vertical sidebar tabs + content */}
            <div className="flex gap-5 items-start">

            {/* ── Left: vertical tab sidebar ── */}
            <div className="w-44 flex-shrink-0">
                <nav className="bg-neutral-900 rounded-xl p-2 flex flex-col gap-1 sticky top-4">
                    {([
                        ['queue', 'Queue'],
                        ['my-reviews', 'My Reviews'],
                        ['accuracy', 'Accuracy'],
                        ['community', 'Community'],
                    ] as [TabKey, string][]).map(([key, label]) => (
                        <button
                            key={key}
                            onClick={() => setTab(key)}
                            className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${tab === key
                                ? 'bg-neutral-800 text-white'
                                : 'text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800/50'
                            }`}
                        >
                            {label}
                        </button>
                    ))}
                </nav>
            </div>

            {/* ── Right: tab content ── */}
            <div className="flex-1 min-w-0">

            {/* ── Queue Tab ── */}
            {tab === 'queue' && (
                <div className="space-y-4">
                    {/* Controls */}
                    <div className="flex flex-wrap gap-3 items-center justify-between">
                        <div className="flex flex-wrap gap-1.5">
                            {([
                                ['unreviewed', 'Pending'],
                                ['reviewed', 'Reviewed'],
                                ['appealed', 'Appealed'],
                                ['finalized', 'Finalized'],
                                ['all', 'All'],
                            ] as [FilterKey, string][]).map(([k, lbl]) => (
                                <button
                                    key={k}
                                    onClick={() => setFilter(k)}
                                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all border ${filter === k
                                        ? 'bg-orange-700 text-white border-orange-600'
                                        : 'bg-transparent text-neutral-400 border-neutral-700 hover:border-neutral-500'
                                        }`}
                                >
                                    {lbl}
                                </button>
                            ))}
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-neutral-500">Sort:</span>
                            <select
                                value={sortKey}
                                onChange={e => setSortKey(e.target.value as SortKey)}
                                className="text-sm border border-neutral-700 rounded-lg px-2 py-1.5 bg-neutral-900 text-neutral-300 focus:outline-none focus:ring-2 focus:ring-neutral-600"
                            >
                                <option value="oldest">Oldest First</option>
                                <option value="newest">Newest First</option>
                                <option value="most_supported">Most Supported</option>
                                <option value="most_challenged">Most Challenged</option>
                            </select>
                        </div>
                    </div>

                    {/* Keyboard hint */}
                    {selectedReport && (
                        <div className="flex items-center gap-2 text-xs text-neutral-600">
                            <BoltIcon className="h-3 w-3" />
                            Shortcuts:
                            <kbd className="bg-neutral-800 px-1.5 py-0.5 rounded border border-neutral-700 text-neutral-400">P</kbd> Pass ·
                            <kbd className="bg-neutral-800 px-1.5 py-0.5 rounded border border-neutral-700 text-neutral-400">N</kbd> Needs Evidence ·
                            <kbd className="bg-neutral-800 px-1.5 py-0.5 rounded border border-neutral-700 text-neutral-400">R</kbd> Reject ·
                            <kbd className="bg-neutral-800 px-1.5 py-0.5 rounded border border-neutral-700 text-neutral-400">Esc</kbd> Deselect
                        </div>
                    )}

                    {/* Report list */}
                    {loading ? (
                        <div className="space-y-3">
                            {[1, 2, 3].map(i => <div key={i} className="animate-pulse bg-neutral-900 rounded-lg h-28" />)}
                        </div>
                    ) : sortedReports.length === 0 ? (
                        <div className="text-center py-16 rounded-2xl border border-neutral-800 bg-neutral-950">
                            <DocumentMagnifyingGlassIcon className="h-12 w-12 text-neutral-700 mx-auto mb-3" />
                            <p className="text-neutral-400 font-medium">No reports to show</p>
                            <p className="text-neutral-600 text-sm mt-1">Try a different filter.</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {sortedReports.map(report => (
                                <ReportCard
                                    key={report.id}
                                    report={report}
                                    selected={selectedReport?.id === report.id}
                                    reviewing={reviewingId === report.id}
                                    batchChecked={batchSelected.has(report.id)}
                                    walletAddress={walletAddress}
                                    onToggle={() => setSelectedReport(selectedReport?.id === report.id ? null : report)}
                                    onDecision={handleSetDecision}
                                    onViewActor={() => setActorSlideOver(report.reporter)}
                                    onBatchToggle={() => {
                                        setBatchSelected(prev => {
                                            const next = new Set(prev);
                                            if (next.has(report.id)) next.delete(report.id);
                                            else next.add(report.id);
                                            return next;
                                        });
                                    }}
                                />
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* ── My Reviews Tab ── */}
            {tab === 'my-reviews' && (
                <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Decision breakdown */}
                        <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
                            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-3">Decision Breakdown</p>
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                    <span className="text-neutral-300">Review Passed</span>
                                    <span className="font-semibold text-white">{decisionBreakdown.passed}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-neutral-400">Needs Evidence</span>
                                    <span className="font-semibold text-neutral-300">{decisionBreakdown.needsEvidence}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-neutral-400">Reject Spam</span>
                                    <span className="font-semibold text-neutral-300">{decisionBreakdown.rejected}</span>
                                </div>
                                <div className="border-t border-neutral-800 pt-2 flex justify-between text-sm font-semibold text-white">
                                    <span>Total</span>
                                    <span>{totalReviewed}</span>
                                </div>
                            </div>
                        </div>

                        {/* Streak card */}
                        <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
                            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-3">Review Streak</p>
                            <div className="flex items-center gap-3">
                                <FireIcon className="h-10 w-10" style={{ color: streak > 0 ? '#E84B1A' : '#404040' }} />
                                <div>
                                    <p className="text-3xl font-bold text-white">{streak}</p>
                                    <p className="text-xs text-neutral-500">consecutive days</p>
                                </div>
                            </div>
                            <p className="text-xs text-neutral-600 mt-3">
                                {streak === 0
                                    ? 'Submit a review today to start your streak!'
                                    : streak === 1
                                        ? 'Great start! Review again tomorrow to extend your streak.'
                                        : `${streak} days in a row — keep it up!`}
                            </p>
                        </div>

                        {/* Rep score card */}
                        <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
                            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-3">Reputation</p>
                            <p className="text-3xl font-bold text-white">{reputationScore}</p>
                            <p className="text-xs text-neutral-500 mt-1">Reviewer threshold: 50</p>
                        </div>
                    </div>

                    {/* Reviewed list */}
                    <h3 className="font-semibold text-neutral-300">Your Reviewed Reports</h3>
                    {reports.filter(r => r.reviewDecision !== ReviewerDecision.NONE).length === 0 ? (
                        <div className="text-center py-10 rounded-2xl border border-neutral-800 bg-neutral-950">
                            <EyeIcon className="h-10 w-10 text-neutral-700 mx-auto mb-2" />
                            <p className="text-neutral-500 text-sm">You haven't reviewed any reports yet.</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {reports
                                .filter(r => r.reviewDecision !== ReviewerDecision.NONE)
                                .map(r => {
                                    const isExpanded = selectedReport?.id === r.id;
                                    return (
                                        <div key={r.id} className={`rounded-xl border bg-neutral-950 overflow-hidden transition-all ${isExpanded ? 'border-neutral-600' : 'border-neutral-800 hover:border-neutral-600'}`}>
                                            {/* Header row — click to expand */}
                                            <div
                                                className="p-4 flex items-center justify-between cursor-pointer select-none"
                                                onClick={() => setSelectedReport(isExpanded ? null : r)}
                                            >
                                                <div>
                                                    <p className="text-sm font-medium text-white">Report #{r.id}</p>
                                                    <p className="text-xs text-neutral-500">{formatTimeAgo(r.createdAt)} · By {truncAddr(r.reporter)}</p>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-neutral-800 text-neutral-300">
                                                        {REVIEWER_DECISION_NAMES[r.reviewDecision]}
                                                    </span>
                                                    {r.finalLabel !== FinalLabel.UNREVIEWED && (
                                                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${FINAL_LABEL_COLORS[r.finalLabel]}`}>
                                                            {FINAL_LABEL_NAMES[r.finalLabel]}
                                                        </span>
                                                    )}
                                                    <ChevronDownIcon className={`h-4 w-4 text-neutral-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                                                </div>
                                            </div>
                                            {/* Expanded details */}
                                            {isExpanded && (
                                                <div className="border-t border-neutral-800 px-4 pb-4 pt-3">
                                                    <ReportDetailsPanel report={r} />
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                        </div>
                    )}
                </div>
            )}

            {/* ── Accuracy Tab ── */}
            {tab === 'accuracy' && (
                <div className="space-y-4">
                    <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-6">
                        <div className="flex items-center gap-3 mb-5">
                            <ChartBarIcon className="h-6 w-6 text-neutral-400" />
                            <h3 className="text-lg font-semibold text-white">Review Accuracy Tracker</h3>
                        </div>

                        {accuracyStats.total === 0 ? (
                            <div className="text-center py-8">
                                <p className="text-neutral-500 text-sm">No finalized reports with your decisions yet.</p>
                                <p className="text-neutral-600 text-xs mt-1">
                                    Accuracy is measured by comparing your decision to the moderator's final label.
                                </p>
                            </div>
                        ) : (
                            <>
                                <div className="flex items-center gap-6 mb-6">
                                    {/* Donut */}
                                    <div className="relative h-24 w-24 flex-shrink-0">
                                        <svg className="h-24 w-24 -rotate-90" viewBox="0 0 36 36">
                                            <circle cx="18" cy="18" r="15.9" fill="none" stroke="#262626" strokeWidth="3.5" />
                                            <circle
                                                cx="18" cy="18" r="15.9" fill="none"
                                                stroke={accuracyStats.pct >= 50 ? '#ffffff' : '#E84B1A'}
                                                strokeWidth="3.5"
                                                strokeDasharray={`${accuracyStats.pct} ${100 - accuracyStats.pct}`}
                                                strokeLinecap="round"
                                            />
                                        </svg>
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <span className="text-lg font-bold text-white">
                                                {accuracyStats.pct}%
                                            </span>
                                        </div>
                                    </div>
                                    <div className="space-y-1">
                                        <p className="text-sm text-neutral-400">
                                            <span className="font-semibold text-white">{accuracyStats.correct}</span> correct out of{' '}
                                            <span className="font-semibold text-white">{accuracyStats.total}</span> finalized reports
                                        </p>
                                        <p className="text-xs text-neutral-500">
                                            {accuracyStats.pct >= 70
                                                ? 'Good accuracy — keep it up.'
                                                : accuracyStats.pct >= 50
                                                    ? 'Average accuracy — review more carefully.'
                                                    : 'Low accuracy — incorrect decisions may cost reputation.'}
                                        </p>
                                    </div>
                                </div>

                                <div className="bg-neutral-900 rounded-lg p-4">
                                    <p className="text-xs text-neutral-500 uppercase tracking-wider mb-2">Matching Logic</p>
                                    <ul className="text-xs text-neutral-400 space-y-1.5">
                                        <li>· Final: <strong className="text-neutral-300">Corroborated</strong> → Expected: <strong className="text-neutral-300">Review Passed</strong></li>
                                        <li>· Final: <strong className="text-neutral-300">False / Manipulated</strong> → Expected: <strong className="text-neutral-300">Reject Spam</strong></li>
                                        <li>· Final: <strong className="text-neutral-300">Needs Evidence / Disputed</strong> → Expected: <strong className="text-neutral-300">Needs Evidence</strong></li>
                                    </ul>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            )}

            {/* ── Community Tab ── */}
            {tab === 'community' && (
                <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Engagement stats */}
                        <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
                            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-3">Engagement Stats</p>
                            <div className="space-y-3">
                                {[
                                    ['Avg. Supporters / Report', communityStats.avgSupport],
                                    ['Avg. Challengers / Report', communityStats.avgChallenge],
                                    ['Appeals Rate', `${communityStats.appealsRate}%`],
                                    ['Total Reports', String(reports.length)],
                                ].map(([label, val]) => (
                                    <div key={label} className="flex justify-between text-sm">
                                        <span className="text-neutral-400">{label}</span>
                                        <span className="font-semibold text-white">{val}</span>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Label distribution */}
                        <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
                            <p className="text-xs text-neutral-500 uppercase tracking-wider mb-3">Label Distribution</p>
                            <div className="space-y-2.5">
                                {communityStats.labelDist.map(({ label, count, pct }) => (
                                    <div key={label}>
                                        <div className="flex justify-between text-xs text-neutral-400 mb-1">
                                            <span>{FINAL_LABEL_NAMES[label]}</span>
                                            <span>{count} ({pct}%)</span>
                                        </div>
                                        <div className="h-1.5 bg-neutral-800 rounded-full">
                                            <div
                                                className="h-1.5 rounded-full transition-all bg-neutral-400"
                                                style={{ width: `${pct}%`, backgroundColor: label === FinalLabel.FALSE_OR_MANIPULATED ? '#E84B1A' : undefined }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            </div> {/* end right content */}
            </div> {/* end two-column layout */}

            {/* Reviewer Guidelines info box */}
            <div className="rounded-2xl border border-neutral-800 bg-neutral-950 p-5">
                <div className="flex items-start gap-3">
                    <ExclamationTriangleIcon className="h-5 w-5 text-neutral-500 mt-0.5 flex-shrink-0" />
                    <div>
                        <h3 className="font-medium text-white text-sm">Reviewer Guidelines</h3>
                        <ul className="text-sm text-neutral-400 mt-1.5 space-y-1 list-disc pl-4">
                            <li><strong className="text-neutral-300">Review Passed:</strong> Evidence appears credible and meets submission standards.</li>
                            <li><strong className="text-neutral-300">Needs Evidence:</strong> Report lacks sufficient supporting documentation.</li>
                            <li><strong className="text-neutral-300">Reject Spam:</strong> Report is spam, abusive, or clearly fabricated.</li>
                            <li>Your decision helps moderators make the final call. Accuracy affects your reputation.</li>
                            <li>Reviewer badge requires <strong className="text-neutral-300">Rep ≥ 50</strong>. Badge deactivates if rep drops below threshold.</li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Actor Slide-Over */}
            {actorSlideOver && (
                <ActorDeepDivePanel wallet={actorSlideOver} onClose={() => setActorSlideOver(null)} />
            )}

            {/* Batch Bottom Bar */}
            {batchSelected.size > 0 && (
                <div className="fixed bottom-0 left-0 right-0 z-40 bg-neutral-950 border-t border-neutral-800 shadow-lg px-6 py-4">
                    <div className="max-w-5xl mx-auto flex items-center justify-between gap-4">
                        <p className="text-sm font-medium text-neutral-300">
                            {batchSelected.size} report(s) selected
                        </p>
                        <div className="flex items-center gap-3">
                            <select
                                value={batchDecision}
                                onChange={e => setBatchDecision(Number(e.target.value) as ReviewerDecision)}
                                className="text-sm border border-neutral-700 rounded-lg px-3 py-2 bg-neutral-900 text-neutral-300 focus:outline-none focus:ring-2 focus:ring-neutral-600"
                            >
                                <option value={ReviewerDecision.REVIEW_PASSED}>Review Passed</option>
                                <option value={ReviewerDecision.NEEDS_EVIDENCE}>Needs Evidence</option>
                                <option value={ReviewerDecision.REJECT_SPAM}>Reject Spam</option>
                            </select>
                            <button
                                onClick={handleBatchSubmit}
                                disabled={batchSubmitting}
                                className="px-5 py-2 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 hover:opacity-90"
                                style={{ backgroundColor: '#E84B1A', color: '#fff' }}
                            >
                                {batchSubmitting ? 'Submitting…' : 'Submit Batch'}
                            </button>
                            <button
                                onClick={() => setBatchSelected(new Set())}
                                className="px-3 py-2 border border-neutral-700 rounded-lg text-sm text-neutral-400 hover:text-white hover:border-neutral-500 transition-colors"
                            >
                                Clear
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ReviewerDashboard;
