// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/CovertProtocol.sol";
import "../src/CovertBadges.sol";

/**
 * @title GrantRolesScript
 * @notice Assigns Reviewer / Moderator roles and mints the corresponding SBT badges
 *         for local Anvil development.
 *
 * Reviewers  : accounts 2, 4
 * Moderators : accounts 3, 6, 9
 * Normal users: accounts 1, 5, 7, 8  (account 0 is the deployer / admin)
 *
 * Usage (from contracts/ directory, after Anvil + Deploy have run):
 *   forge script script/GrantRoles.s.sol:GrantRolesScript \
 *     --rpc-url http://127.0.0.1:8545 --broadcast
 */
contract GrantRolesScript is Script {
    // ── Anvil deployer (overridable via PRIVATE_KEY env var) ──────────────────
    address constant DEPLOYER = 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266;

    // ── Reviewers (accounts 2, 4) ──────────────────────────────────────────────
    address constant REVIEWER_2 = 0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC;
    address constant REVIEWER_4 = 0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65;

    // ── Moderators (accounts 3, 6, 9) ─────────────────────────────────────────
    address constant MODERATOR_3 = 0x90F79bf6EB2c4f870365E785982E1f101E93b906;
    address constant MODERATOR_6 = 0x976EA74026E726554dB657fA54763abd0C3a0aa9;
    address constant MODERATOR_9 = 0xa0Ee7A142d267C1f36714E4a8F75612F20a79720;

    function run() external {
        // Default to Anvil account #0; override with PRIVATE_KEY env var for real deployments
        uint256 DEPLOYER_KEY = vm.envOr("PRIVATE_KEY", uint256(0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80));

        // Read deployed addresses from env (set by Deploy script) or fall back
        // to the deterministic addresses a fresh Anvil + DeployLocalScript produces.
        address protocolAddr = vm.envOr(
            "COVERT_PROTOCOL_ADDRESS",
            address(0xDc64a140Aa3E981100a9becA4E685f962f0cF6C9)
        );
        address badgesAddr = vm.envOr(
            "COVERT_BADGES_ADDRESS",
            address(0xCf7Ed3AccA5a467e9e704C703E8D87F634fB0Fc9)
        );

        CovertProtocol protocol = CovertProtocol(protocolAddr);
        CovertBadges   badges   = CovertBadges(badgesAddr);

        console.log("=== C.O.V.E.R.T Role Setup ===");
        console.log("Protocol  :", protocolAddr);
        console.log("Badges    :", badgesAddr);
        console.log("Reviewer  (acct 2) :", REVIEWER_2);
        console.log("Reviewer  (acct 4) :", REVIEWER_4);
        console.log("Moderator (acct 3) :", MODERATOR_3);
        console.log("Moderator (acct 6) :", MODERATOR_6);
        console.log("Moderator (acct 9) :", MODERATOR_9);
        console.log("==============================");

        vm.startBroadcast(DEPLOYER_KEY);

        // ── 1. Grant REVIEWER_ROLE to accounts 2 and 4 ─────────────────────────
        // Deployer holds AUTOMATION_ROLE, which is role-admin of REVIEWER_ROLE.
        protocol.grantRole(protocol.REVIEWER_ROLE(), REVIEWER_2);
        console.log("[OK] Granted REVIEWER_ROLE  -> account (2)");
        protocol.grantRole(protocol.REVIEWER_ROLE(), REVIEWER_4);
        console.log("[OK] Granted REVIEWER_ROLE  -> account (4)");

        // ── 2. Grant MODERATOR_ROLE to accounts 3, 6, and 9 ───────────────────
        // Deployer holds DEFAULT_ADMIN_ROLE, which is role-admin of MODERATOR_ROLE.
        protocol.grantRole(protocol.MODERATOR_ROLE(), MODERATOR_3);
        console.log("[OK] Granted MODERATOR_ROLE -> account (3)");
        protocol.grantRole(protocol.MODERATOR_ROLE(), MODERATOR_6);
        console.log("[OK] Granted MODERATOR_ROLE -> account (6)");
        protocol.grantRole(protocol.MODERATOR_ROLE(), MODERATOR_9);
        console.log("[OK] Granted MODERATOR_ROLE -> account (9)");

        // ── 3. Revoke MODERATOR_ROLE from deployer (account 0) ─────────────────
        // The constructor auto-granted it; remove it so deployer is admin-only.
        protocol.revokeRole(protocol.MODERATOR_ROLE(), DEPLOYER);
        console.log("[OK] Revoked MODERATOR_ROLE from deployer (account 0)");

        // ── 4. Mint SBT badges ──────────────────────────────────────────────────
        // Deployer holds BADGE_MANAGER_ROLE on CovertBadges.
        badges.mintBadge(REVIEWER_2,  CovertBadges.BadgeType.REVIEWER_BADGE);
        console.log("[OK] Minted REVIEWER_BADGE  -> account (2)");
        badges.mintBadge(REVIEWER_4,  CovertBadges.BadgeType.REVIEWER_BADGE);
        console.log("[OK] Minted REVIEWER_BADGE  -> account (4)");

        badges.mintBadge(MODERATOR_3, CovertBadges.BadgeType.MODERATOR_BADGE);
        console.log("[OK] Minted MODERATOR_BADGE -> account (3)");
        badges.mintBadge(MODERATOR_6, CovertBadges.BadgeType.MODERATOR_BADGE);
        console.log("[OK] Minted MODERATOR_BADGE -> account (6)");
        badges.mintBadge(MODERATOR_9, CovertBadges.BadgeType.MODERATOR_BADGE);
        console.log("[OK] Minted MODERATOR_BADGE -> account (9)");

        vm.stopBroadcast();

        console.log("\n=== Setup complete ===");
        console.log("Reviewers  (accts 2, 4)  :", REVIEWER_2);
        console.log("                          :", REVIEWER_4);
        console.log("Moderators (accts 3, 6, 9):", MODERATOR_3);
        console.log("                           :", MODERATOR_6);
        console.log("                           :", MODERATOR_9);
        console.log("Normal users: accounts 1, 5, 7, 8 (deployer 0 is admin).");
    }
}
