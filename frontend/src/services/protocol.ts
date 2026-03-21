/**
 * C.O.V.E.R.T - Protocol Service
 *
 * Interacts with COVCredits, CovertBadges, and CovertProtocol contracts.
 */

import { ethers, BrowserProvider, Contract, Signer, formatEther, parseEther } from 'ethers';
import {
    COV_CREDITS_ABI,
    COVERT_BADGES_ABI,
    COVERT_PROTOCOL_ABI,
    type ProtocolReport,
    Visibility,
    ReviewerDecision,
    FinalLabel,
    AppealOutcome,
    BadgeType,
} from '../types/protocol';

export interface ProtocolConfig {
    covCreditsAddress: string;
    covertBadgesAddress: string;
    covertProtocolAddress: string;
}

export interface UserProtocolState {
    covBalance: string;
    lockedBalance: string;
    welcomeClaimed: boolean;
    badges: { type: BadgeType; active: boolean; tokenId: string }[];
}

const DEFAULT_USER_STATE: UserProtocolState = {
    covBalance: '0',
    lockedBalance: '0',
    welcomeClaimed: false,
    badges: [],
};

class ProtocolService {
    private provider: BrowserProvider | null = null;
    private signer: Signer | null = null;
    private covCredits: Contract | null = null;
    private covBadges: Contract | null = null;
    private covProtocol: Contract | null = null;
    private config: ProtocolConfig | null = null;

    configure(config: ProtocolConfig) {
        this.config = config;
    }

    async connect() {
        try {
            if (!window.ethereum) throw new Error('No wallet found');
            this.provider = new BrowserProvider(window.ethereum);
            this.signer = await this.provider.getSigner();

            if (!this.config) throw new Error('Protocol not configured');

            if (this.config.covCreditsAddress) {
                this.covCredits = new Contract(this.config.covCreditsAddress, COV_CREDITS_ABI, this.signer);
            }
            if (this.config.covertBadgesAddress) {
                this.covBadges = new Contract(this.config.covertBadgesAddress, COVERT_BADGES_ABI, this.signer);
            }
            if (this.config.covertProtocolAddress) {
                this.covProtocol = new Contract(this.config.covertProtocolAddress, COVERT_PROTOCOL_ABI, this.signer);
            }
        } catch (err) {
            console.error('[Protocol] connect failed:', err);
            throw err;
        }
    }

    isConfigured(): boolean {
        return !!(this.config?.covCreditsAddress && this.config?.covertProtocolAddress);
    }

    async getSignerAddress(): Promise<string | null> {
        try {
            if (!this.signer) return null;
            return await this.signer.getAddress();
        } catch (err) {
            console.error('[Protocol] getSignerAddress failed:', err);
            throw err;
        }
    }

    // ─────────── Read: User State ───────────

    async getUserState(address: string): Promise<UserProtocolState> {
        try {
            if (!this.covCredits || !this.covProtocol) throw new Error('Not connected');

            const [balance, locked, claimed] = await Promise.all([
                this.covCredits.balanceOf(address),
                this.covProtocol.lockedBalance(address),
                this.covCredits.welcomeClaimed(address),
            ]);

            let badges: UserProtocolState['badges'] = [];
            if (this.covBadges) {
                try {
                    const [tokenIds, activeStates] = await this.covBadges.getUserBadges(address);
                    badges = Array.from({ length: 6 }, (_, i) => ({
                        type: i as BadgeType,
                        active: activeStates[i],
                        tokenId: tokenIds[i].toString(),
                    })).filter((b) => b.tokenId !== '0');
                } catch {
                    // Badges contract may not be deployed
                }
            }

            return {
                covBalance: formatEther(balance),
                lockedBalance: formatEther(locked),
                welcomeClaimed: claimed,
                badges,
            };
        } catch (err) {
            console.error('[Protocol] getUserState failed:', err);
            return DEFAULT_USER_STATE;
        }
    }

    // ─────────── Read: Reports ───────────

    async getReportCount(): Promise<number> {
        try {
            if (!this.covProtocol) return 0;
            const count = await this.covProtocol.nextReportId();
            return Number(count);
        } catch (err) {
            console.error('[Protocol] getReportCount failed:', err);
            return 0;
        }
    }

    async getReport(reportId: number): Promise<ProtocolReport | null> {
        try {
            if (!this.covProtocol) return null;
            const r = await this.covProtocol.getReport(reportId);
            return {
                reporter: r.reporter,
                visibility: Number(r.visibility) as Visibility,
                contentHash: r.contentHash,
                finalLabel: Number(r.finalLabel) as FinalLabel,
                reviewDecision: Number(r.reviewDecision) as ReviewerDecision,
                createdAt: Number(r.createdAt),
                reviewedAt: Number(r.reviewedAt),
                finalizedAt: Number(r.finalizedAt),
                hasAppeal: r.hasAppeal,
                appealReasonHash: r.appealReasonHash,
                lockedReportStake: r.lockedReportStake,
                lockedAppealBond: r.lockedAppealBond,
            };
        } catch (err) {
            console.error('[Protocol] getReport failed:', err);
            return null;
        }
    }

    async getReportsInRange(start: number, end: number): Promise<(ProtocolReport & { id: number })[]> {
        const reports: (ProtocolReport & { id: number })[] = [];
        for (let i = start; i < end; i++) {
            try {
                const report = await this.getReport(i);
                if (report && report.createdAt > 0) {
                    reports.push({ ...report, id: i });
                }
            } catch {
                break;
            }
        }
        return reports;
    }

    /** Scan on-chain reports to find the numeric ID whose contentHash matches. */
    async getReportIdByHash(contentHash: string): Promise<number | null> {
        if (!this.covProtocol) return null;
        try {
            const count = await this.getReportCount();
            for (let i = 0; i < count; i++) {
                const r = await this.covProtocol.reports(i);
                if (r.contentHash === contentHash) return i;
            }
        } catch (err) {
            console.error('[Protocol] getReportIdByHash failed:', err);
        }
        return null;
    }

    async getSupporterCount(reportId: number): Promise<number> {
        try {
            if (!this.covProtocol) return 0;
            return Number(await this.covProtocol.getSupporterCount(reportId));
        } catch (err) {
            console.error('[Protocol] getSupporterCount failed:', err);
            return 0;
        }
    }

    async getChallengerCount(reportId: number): Promise<number> {
        try {
            if (!this.covProtocol) return 0;
            return Number(await this.covProtocol.getChallengerCount(reportId));
        } catch (err) {
            console.error('[Protocol] getChallengerCount failed:', err);
            return 0;
        }
    }

    async getSupporters(reportId: number): Promise<string[]> {
        try {
            if (!this.covProtocol) return [];
            const result = await this.covProtocol.getSupporters(reportId);
            return Array.from(result) as string[];
        } catch (err) {
            console.error('[Protocol] getSupporters failed:', err);
            return [];
        }
    }

    async getChallengers(reportId: number): Promise<string[]> {
        try {
            if (!this.covProtocol) return [];
            const result = await this.covProtocol.getChallengers(reportId);
            return Array.from(result) as string[];
        } catch (err) {
            console.error('[Protocol] getChallengers failed:', err);
            return [];
        }
    }

    // ─────────── Write: Welcome ───────────

    async claimWelcome(): Promise<string> {
        try {
            if (!this.covProtocol) throw new Error('Not connected');
            const tx = await this.covProtocol.claimWelcome();
            const receipt = await tx.wait();
            return receipt.hash;
        } catch (err) {
            console.error('[Protocol] claimWelcome failed:', err);
            throw err;
        }
    }

    // ─────────── Write: Reports ───────────

    async createReport(visibility: Visibility, contentHash: string): Promise<string> {
        try {
            if (!this.covProtocol) throw new Error('Not connected');
            const tx = await this.covProtocol.createReport(visibility, contentHash);
            const receipt = await tx.wait();
            return receipt.hash;
        } catch (err) {
            console.error('[Protocol] createReport failed:', err);
            throw err;
        }
    }

    async supportReport(reportId: number, reasonHash: string): Promise<string> {
        try {
            if (!this.covProtocol) throw new Error('Not connected');
            const tx = await this.covProtocol.support(reportId, reasonHash);
            const receipt = await tx.wait();
            return receipt.hash;
        } catch (err) {
            console.error('[Protocol] supportReport failed:', err);
            throw err;
        }
    }

    async challengeReport(reportId: number, reasonHash: string): Promise<string> {
        try {
            if (!this.covProtocol) throw new Error('Not connected');
            const tx = await this.covProtocol.challenge(reportId, reasonHash);
            const receipt = await tx.wait();
            return receipt.hash;
        } catch (err) {
            console.error('[Protocol] challengeReport failed:', err);
            throw err;
        }
    }

    // ─────────── Write: Review ───────────

    async setReviewDecision(reportId: number, decision: ReviewerDecision): Promise<string> {
        try {
            if (!this.covProtocol) throw new Error('Not connected');
            const tx = await this.covProtocol.setReviewDecision(reportId, decision);
            const receipt = await tx.wait();
            return receipt.hash;
        } catch (err) {
            console.error('[Protocol] setReviewDecision failed:', err);
            throw err;
        }
    }

    // ─────────── Write: Appeal ───────────

    async appeal(reportId: number, appealReasonHash: string): Promise<string> {
        try {
            if (!this.covProtocol) throw new Error('Not connected');
            const tx = await this.covProtocol.appeal(reportId, appealReasonHash);
            const receipt = await tx.wait();
            return receipt.hash;
        } catch (err) {
            console.error('[Protocol] appeal failed:', err);
            throw err;
        }
    }

    // ─────────── Write: Moderation ───────────

    async markMalicious(reportId: number, actor: string, isMalicious: boolean): Promise<string> {
        try {
            if (!this.covProtocol) throw new Error('Not connected');
            const tx = await this.covProtocol.markMalicious(reportId, actor, isMalicious);
            const receipt = await tx.wait();
            return receipt.hash;
        } catch (err) {
            console.error('[Protocol] markMalicious failed:', err);
            throw err;
        }
    }

    async finalizeReport(
        reportId: number,
        label: FinalLabel,
        appealOutcome: AppealOutcome,
    ): Promise<string> {
        try {
            if (!this.covProtocol) throw new Error('Not connected');
            const tx = await this.covProtocol.finalizeReport(reportId, label, appealOutcome);
            const receipt = await tx.wait();
            return receipt.hash;
        } catch (err) {
            console.error('[Protocol] finalizeReport failed:', err);
            throw err;
        }
    }
}

export const protocolService = new ProtocolService();
export default protocolService;
