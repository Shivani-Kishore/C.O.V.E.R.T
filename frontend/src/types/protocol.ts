/**
 * C.O.V.E.R.T - Protocol Contract ABIs and Types
 *
 * Type definitions and ABI fragments for COVCredits, CovertBadges, and CovertProtocol.
 */

// ─────────── Enums (mirroring Solidity) ───────────

export enum Visibility {
    PUBLIC = 0,
    PRIVATE = 1,
}

export enum ReviewerDecision {
    NONE = 0,
    NEEDS_EVIDENCE = 1,
    REVIEW_PASSED = 2,
    REJECT_SPAM = 3,
}

export enum FinalLabel {
    UNREVIEWED = 0,
    NEEDS_EVIDENCE = 1,
    CORROBORATED = 2,
    DISPUTED = 3,
    FALSE_OR_MANIPULATED = 4,
}

export enum AppealOutcome {
    NONE = 0,
    APPEAL_WON = 1,
    APPEAL_LOST = 2,
    APPEAL_ABUSIVE = 3,
}

export enum BadgeType {
    TIER_0_NEW = 0,
    TIER_1_REGULAR = 1,
    TIER_2_TRUSTED = 2,
    TIER_3_POWER = 3,
    REVIEWER_BADGE = 4,
    MODERATOR_BADGE = 5,
}

// ─────────── Interfaces ───────────

export interface ProtocolReport {
    reporter: string;
    visibility: Visibility;
    contentHash: string;
    finalLabel: FinalLabel;
    reviewDecision: ReviewerDecision;
    createdAt: number;
    reviewedAt: number;
    finalizedAt: number;
    hasAppeal: boolean;
    appealReasonHash: string;
    lockedReportStake: bigint;
    lockedAppealBond: bigint;
}

export interface BadgeState {
    tokenIds: bigint[];
    activeStates: boolean[];
}

// ─────────── Label/Decision Display Helpers ───────────

export const FINAL_LABEL_NAMES: Record<FinalLabel, string> = {
    [FinalLabel.UNREVIEWED]: 'Unreviewed',
    [FinalLabel.NEEDS_EVIDENCE]: 'Needs Evidence',
    [FinalLabel.CORROBORATED]: 'Corroborated',
    [FinalLabel.DISPUTED]: 'Disputed',
    [FinalLabel.FALSE_OR_MANIPULATED]: 'False / Manipulated',
};

export const FINAL_LABEL_COLORS: Record<FinalLabel, string> = {
    [FinalLabel.UNREVIEWED]: 'bg-neutral-800 text-neutral-400',
    [FinalLabel.NEEDS_EVIDENCE]: 'bg-yellow-900/40 text-yellow-400',
    [FinalLabel.CORROBORATED]: 'bg-green-900/40 text-green-400',
    [FinalLabel.DISPUTED]: 'bg-orange-900/40 text-orange-400',
    [FinalLabel.FALSE_OR_MANIPULATED]: 'bg-red-900/40 text-red-400',
};

export const REVIEWER_DECISION_NAMES: Record<ReviewerDecision, string> = {
    [ReviewerDecision.NONE]: 'None',
    [ReviewerDecision.NEEDS_EVIDENCE]: 'Needs Evidence',
    [ReviewerDecision.REVIEW_PASSED]: 'Review Passed',
    [ReviewerDecision.REJECT_SPAM]: 'Reject (Spam)',
};

export const APPEAL_OUTCOME_NAMES: Record<AppealOutcome, string> = {
    [AppealOutcome.NONE]: 'None',
    [AppealOutcome.APPEAL_WON]: 'Appeal Won',
    [AppealOutcome.APPEAL_LOST]: 'Appeal Lost',
    [AppealOutcome.APPEAL_ABUSIVE]: 'Appeal Abusive',
};

export const BADGE_TYPE_NAMES: Record<BadgeType, string> = {
    [BadgeType.TIER_0_NEW]: 'New',
    [BadgeType.TIER_1_REGULAR]: 'Regular',
    [BadgeType.TIER_2_TRUSTED]: 'Trusted',
    [BadgeType.TIER_3_POWER]: 'Power',
    [BadgeType.REVIEWER_BADGE]: 'Reviewer',
    [BadgeType.MODERATOR_BADGE]: 'Moderator',
};

// ─────────── Stake Constants (in COV, not wei) ───────────

export const STAKES = {
    REPORT_PUBLIC: 10,
    REPORT_PRIVATE: 6,
    SUPPORT: 1,
    CHALLENGE: 3,
    APPEAL_BOND: 8,
    WELCOME_GRANT: 30,
} as const;

// ─────────── ABI Fragments ───────────

export const COV_CREDITS_ABI = [
    'function name() view returns (string)',
    'function symbol() view returns (string)',
    'function decimals() view returns (uint8)',
    'function totalSupply() view returns (uint256)',
    'function balanceOf(address account) view returns (uint256)',
    'function welcomeClaimed(address) view returns (bool)',
    'function WELCOME_GRANT() view returns (uint256)',
    'function MAX_SUPPLY() view returns (uint256)',
    'event WelcomeGranted(address indexed user, uint256 amount)',
    'event Minted(address indexed to, uint256 amount)',
    'event Burned(address indexed from, uint256 amount)',
];

export const COVERT_BADGES_ABI = [
    'function isBadgeActive(address user, uint8 badgeType) view returns (bool)',
    'function getUserBadges(address user) view returns (uint256[6] tokenIds, bool[6] activeStates)',
    'function badgeTokenId(address, uint8) view returns (uint256)',
    'event BadgeMinted(address indexed user, uint8 badgeType, uint256 tokenId)',
    'event BadgeActivationChanged(address indexed user, uint8 badgeType, uint256 tokenId, bool isActive)',
];

export const COVERT_PROTOCOL_ABI = [
    // Constants
    'function REPORT_STAKE_PUBLIC() view returns (uint256)',
    'function REPORT_STAKE_PRIVATE() view returns (uint256)',
    'function SUPPORT_STAKE() view returns (uint256)',
    'function CHALLENGE_STAKE() view returns (uint256)',
    'function APPEAL_BOND() view returns (uint256)',

    // State
    'function nextReportId() view returns (uint256)',
    'function treasury() view returns (address)',
    'function lockedBalance(address) view returns (uint256)',

    // Report struct getter
    'function reports(uint256) view returns (address reporter, uint8 visibility, bytes32 contentHash, uint8 finalLabel, uint8 reviewDecision, uint64 createdAt, uint64 reviewedAt, uint64 finalizedAt, bool hasAppeal, bytes32 appealReasonHash, uint256 lockedReportStake, uint256 lockedAppealBond)',
    'function getReport(uint256 reportId) view returns (tuple(address reporter, uint8 visibility, bytes32 contentHash, uint8 finalLabel, uint8 reviewDecision, uint64 createdAt, uint64 reviewedAt, uint64 finalizedAt, bool hasAppeal, bytes32 appealReasonHash, uint256 lockedReportStake, uint256 lockedAppealBond))',

    // Per-report mappings
    'function hasSupported(uint256, address) view returns (bool)',
    'function hasChallenged(uint256, address) view returns (bool)',
    'function lockedSupportStake(uint256, address) view returns (uint256)',
    'function lockedChallengeStake(uint256, address) view returns (uint256)',
    'function malicious(uint256, address) view returns (bool)',

    // View helpers
    'function getSupporterCount(uint256 reportId) view returns (uint256)',
    'function getChallengerCount(uint256 reportId) view returns (uint256)',
    'function getSupporters(uint256 reportId) view returns (address[])',
    'function getChallengers(uint256 reportId) view returns (address[])',

    // Write functions
    'function claimWelcome()',
    'function createReport(uint8 visibility, bytes32 contentHash)',
    'function support(uint256 reportId, bytes32 reasonHash)',
    'function challenge(uint256 reportId, bytes32 reasonHash)',
    'function setReviewDecision(uint256 reportId, uint8 decision)',
    'function appeal(uint256 reportId, bytes32 appealReasonHash)',
    'function markMalicious(uint256 reportId, address actor, bool isMalicious)',
    'function finalizeReport(uint256 reportId, uint8 finalLabel, uint8 appealOutcome)',

    // Events
    'event WelcomeClaimed(address indexed user, uint256 amount)',
    'event ReportCreated(uint256 indexed reportId, address indexed reporter, uint8 visibility, uint256 stake, bytes32 contentHash)',
    'event Supported(uint256 indexed reportId, address indexed user, bytes32 reasonHash)',
    'event Challenged(uint256 indexed reportId, address indexed user, bytes32 reasonHash)',
    'event ReviewDecisionSet(uint256 indexed reportId, address indexed reviewer, uint8 decision)',
    'event Appealed(uint256 indexed reportId, address indexed reporter, bytes32 appealReasonHash)',
    'event MarkedMalicious(uint256 indexed reportId, address indexed actor, bool isMalicious)',
    'event Finalized(uint256 indexed reportId, address indexed moderator, uint8 finalLabel, uint8 appealOutcome)',
    'event StakeReturned(uint256 indexed reportId, address indexed user, uint256 amount, bytes32 stakeType)',
    'event StakeSlashed(uint256 indexed reportId, address indexed user, uint256 amount, bytes32 stakeType)',
];
