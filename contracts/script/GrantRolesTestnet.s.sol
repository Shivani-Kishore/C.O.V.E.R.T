// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/CovertProtocol.sol";
import "../src/CovertBadges.sol";

/**
 * @title GrantRolesTestnet
 * @notice Grants REVIEWER_ROLE / MODERATOR_ROLE on CovertProtocol
 *         AND mints the corresponding SBT badges on CovertBadges
 *         so the frontend routes users to the correct dashboard.
 *
 * Required .env variables:
 *   PRIVATE_KEY            – deployer private key (must hold DEFAULT_ADMIN_ROLE)
 *   REVIEWER_ADDRESS_1     – 0x-prefixed wallet address
 *   REVIEWER_ADDRESS_2     – 0x-prefixed wallet address
 *   MODERATOR_ADDRESS_1    – 0x-prefixed wallet address
 *   MODERATOR_ADDRESS_2    – 0x-prefixed wallet address
 *
 * Usage:
 *   forge script script/GrantRolesTestnet.s.sol --rpc-url https://sepolia.base.org --broadcast
 */
contract GrantRolesTestnet is Script {
    address constant PROTOCOL = 0x5B7AB21B2656BD187c3B544937eac9f36d901CbA;
    address constant BADGES   = 0x81ec2Fe3467535fd8e3A8a5bc00Bc226f2fedda4;

    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");
        address reviewer1   = vm.envAddress("REVIEWER_ADDRESS_1");
        address reviewer2   = vm.envAddress("REVIEWER_ADDRESS_2");
        address moderator1  = vm.envAddress("MODERATOR_ADDRESS_1");
        address moderator2  = vm.envAddress("MODERATOR_ADDRESS_2");

        CovertProtocol protocol = CovertProtocol(PROTOCOL);
        CovertBadges   badges   = CovertBadges(BADGES);

        console.log("=== GrantRolesTestnet ===");
        console.log("Protocol:", PROTOCOL);
        console.log("Badges:  ", BADGES);

        vm.startBroadcast(deployerKey);

        // ── Reviewer 1 ──
        protocol.grantRole(protocol.REVIEWER_ROLE(), reviewer1);
        badges.mintBadge(reviewer1, CovertBadges.BadgeType.REVIEWER_BADGE);
        console.log("[OK] Reviewer 1:", reviewer1);

        // ── Reviewer 2 ──
        protocol.grantRole(protocol.REVIEWER_ROLE(), reviewer2);
        badges.mintBadge(reviewer2, CovertBadges.BadgeType.REVIEWER_BADGE);
        console.log("[OK] Reviewer 2:", reviewer2);

        // ── Moderator 1 ──
        protocol.grantRole(protocol.MODERATOR_ROLE(), moderator1);
        badges.mintBadge(moderator1, CovertBadges.BadgeType.MODERATOR_BADGE);
        console.log("[OK] Moderator 1:", moderator1);

        // ── Moderator 2 ──
        protocol.grantRole(protocol.MODERATOR_ROLE(), moderator2);
        badges.mintBadge(moderator2, CovertBadges.BadgeType.MODERATOR_BADGE);
        console.log("[OK] Moderator 2:", moderator2);

        vm.stopBroadcast();

        console.log("=== Done ===");
    }
}
