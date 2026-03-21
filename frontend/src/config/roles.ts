/**
 * C.O.V.E.R.T - Role Configuration
 *
 * Maps specific wallet addresses to platform roles.
 * In production, roles are determined by on-chain badge ownership via CovertBadges.
 * This file provides the dev/test fallback using the standard Hardhat/Anvil accounts.
 *
 * Test accounts (Hardhat / Anvil defaults):
 *   0  0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266  — normal user
 *   1  0x70997970C51812dc3A010C7d01b50e0d17dc79C8  — normal user
 *   2  0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC  — reviewer
 *   3  0x90F79bf6EB2c4f870365E785982E1f101E93b906  — moderator
 *   4  0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65  — reviewer
 *   5  0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc  — normal user
 *   6  0x976EA74026E726554dB657fA54763abd0C3a0aa9  — moderator
 *   7  0x14dC79964da2C08b23698B3D3cc7Ca32193d9955  — normal user
 *   8  0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f  — normal user
 *   9  0xa0Ee7A142d267C1f36714E4a8F75612F20a79720  — moderator
 */

export type PlatformRole = 'user' | 'reviewer' | 'moderator';

// All comparisons use lowercase addresses
const REVIEWER_ADDRESSES = new Set([
    '0x3c44cdddb6a900fa2b585dd299e03d12fa4293bc', // Account 2
    '0x15d34aaf54267db7d7c367839aaf71a00a2c6a65', // Account 4
]);

const MODERATOR_ADDRESSES = new Set([
    '0x90f79bf6eb2c4f870365e785982e1f101e93b906', // Account 3
    '0x976ea74026e726554db657fa54763abd0c3a0aa9', // Account 6
    '0xa0ee7a142d267c1f36714e4a8f75612f20a79720', // Account 9
]);

export function getAddressRole(address: string): PlatformRole {
    const lower = address.toLowerCase();
    if (MODERATOR_ADDRESSES.has(lower)) return 'moderator';
    if (REVIEWER_ADDRESSES.has(lower)) return 'reviewer';
    return 'user';
}

export function isReviewerAddress(address: string): boolean {
    return REVIEWER_ADDRESSES.has(address.toLowerCase());
}

export function isModeratorAddress(address: string): boolean {
    return MODERATOR_ADDRESSES.has(address.toLowerCase());
}

/**
 * Minimum review requirements before a report is considered fully assessed.
 *   - At least 1 distinct reviewer must submit a decision.
 *   - At least 2 distinct moderators must finalize.
 */
export const REVIEW_REQUIREMENTS = {
    minReviewers: 1,
    minModerators: 2,
} as const;

/** Human-readable role label. */
export const ROLE_LABELS: Record<PlatformRole, string> = {
    user: 'Reporter',
    reviewer: 'Reviewer',
    moderator: 'Protocol Moderator',
};

/** Orange-tinted badge classes per role. */
export const ROLE_BADGE_STYLES: Record<PlatformRole, string> = {
    user: 'bg-neutral-800 text-neutral-300',
    reviewer: 'bg-blue-900/40 text-blue-400',
    moderator: 'bg-purple-900/40 text-purple-400',
};
