// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/CovertProtocol.sol";

/**
 * @title GrantRolesTestnet
 * @notice Grants REVIEWER_ROLE and MODERATOR_ROLE on Base Sepolia.
 *
 * Required .env variables:
 *   PRIVATE_KEY            – deployer private key (must hold DEFAULT_ADMIN_ROLE)
 *   REVIEWER_ADDRESS_1     – 0x-prefixed wallet address
 *   REVIEWER_ADDRESS_2     – 0x-prefixed wallet address
 *   MODERATOR_ADDRESS_1    – 0x-prefixed wallet address
 *
 * Usage:
 *   forge script script/GrantRolesTestnet.s.sol \
 *     --rpc-url https://sepolia.base.org --broadcast
 */
contract GrantRolesTestnet is Script {
    address constant PROTOCOL = 0x5B7AB21B2656BD187c3B544937eac9f36d901CbA;

    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");
        address reviewer1 = vm.envAddress("REVIEWER_ADDRESS_1");
        address reviewer2 = vm.envAddress("REVIEWER_ADDRESS_2");
        address moderator1 = vm.envAddress("MODERATOR_ADDRESS_1");

        CovertProtocol protocol = CovertProtocol(PROTOCOL);

        console.log("=== GrantRolesTestnet ===");
        console.log("Protocol:", PROTOCOL);
        console.log("Reviewer 1:", reviewer1);
        console.log("Reviewer 2:", reviewer2);
        console.log("Moderator 1:", moderator1);

        vm.startBroadcast(deployerKey);

        protocol.grantRole(protocol.REVIEWER_ROLE(), reviewer1);
        console.log("[OK] Granted REVIEWER_ROLE -> ", reviewer1);

        protocol.grantRole(protocol.REVIEWER_ROLE(), reviewer2);
        console.log("[OK] Granted REVIEWER_ROLE -> ", reviewer2);

        protocol.grantRole(protocol.MODERATOR_ROLE(), moderator1);
        console.log("[OK] Granted MODERATOR_ROLE ->", moderator1);

        vm.stopBroadcast();

        console.log("=== Done ===");
    }
}
