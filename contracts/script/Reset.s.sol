// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/COVCredits.sol";
import "../src/CovertProtocol.sol";

/**
 * @title ResetScript
 * @notice Dev-only script: resets all 10 Hardhat/Anvil test accounts to 30 COV
 *         and re-grants on-chain roles so the protocol is in a known good state.
 *
 * Run after a DB reset:
 *   forge script script/Reset.s.sol --rpc-url http://localhost:8545 --broadcast
 *
 * Requirements:
 *   - Deployer wallet must hold MINTER_ROLE + BURNER_ROLE on COVCredits
 *   - Deployer wallet must hold DEFAULT_ADMIN_ROLE on CovertProtocol
 *   - Set COV_CREDITS_ADDRESS and COVERT_PROTOCOL_ADDRESS in env (or .env)
 */
contract ResetScript is Script {
    uint256 constant TARGET_BALANCE = 30 * 10 ** 18; // 30 COV

    // Standard Hardhat / Anvil accounts (indices 0-9)
    address[10] accounts = [
        0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266, // 0 — user
        0x70997970C51812dc3A010C7d01b50e0d17dc79C8, // 1 — user
        0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC, // 2 — reviewer
        0x90F79bf6EB2c4f870365E785982E1f101E93b906, // 3 — moderator
        0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65, // 4 — reviewer
        0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc, // 5 — user
        0x976EA74026E726554dB657fA54763abd0C3a0aa9, // 6 — moderator
        0x14dC79964da2C08b23698B3D3cc7Ca32193d9955, // 7 — user
        0x23618e81E3f5cdF7f54C3d65f7FBc0aBf5B21E8f, // 8 — user
        0xa0Ee7A142d267C1f36714E4a8F75612F20a79720  // 9 — moderator
    ];

    function run() external {
        uint256 deployerKey = vm.envUint("PRIVATE_KEY");

        address covCreditsAddr   = vm.envOr("COV_CREDITS_ADDRESS",   address(0));
        address covertProtoAddr  = vm.envOr("COVERT_PROTOCOL_ADDRESS", address(0));

        require(covCreditsAddr  != address(0), "COV_CREDITS_ADDRESS not set");
        require(covertProtoAddr != address(0), "COVERT_PROTOCOL_ADDRESS not set");

        COVCredits     covCredits    = COVCredits(covCreditsAddr);
        CovertProtocol covertProtocol = CovertProtocol(covertProtoAddr);

        bytes32 REVIEWER_ROLE  = covertProtocol.REVIEWER_ROLE();
        bytes32 MODERATOR_ROLE = covertProtocol.MODERATOR_ROLE();

        vm.startBroadcast(deployerKey);

        // ── 1. Reset COV balances ─────────────────────────────────────────────
        console.log("\n--- Resetting COV balances to 30 ---");
        for (uint i = 0; i < accounts.length; i++) {
            address acct = accounts[i];
            uint256 current = covCredits.balances(acct);

            // Burn existing balance first (idempotent if 0)
            if (current > 0) {
                covCredits.burn(acct, current);
                console.log("Burned", current / 1e18, "COV from", acct);
            }

            // Mint exactly 30 COV — bypass welcomeClaimed guard by using mint()
            covCredits.mint(acct, TARGET_BALANCE);
            console.log("Minted 30 COV to", acct);
        }

        // ── 2. Re-grant on-chain roles (idempotent) ───────────────────────────
        console.log("\n--- Re-granting on-chain roles ---");

        // Reviewer role → accounts 2, 4
        _grantIfMissing(covertProtocol, REVIEWER_ROLE, accounts[2], "REVIEWER_ROLE -> acct 2");
        _grantIfMissing(covertProtocol, REVIEWER_ROLE, accounts[4], "REVIEWER_ROLE -> acct 4");

        // Moderator role → accounts 3, 6, 9
        _grantIfMissing(covertProtocol, MODERATOR_ROLE, accounts[3], "MODERATOR_ROLE -> acct 3");
        _grantIfMissing(covertProtocol, MODERATOR_ROLE, accounts[6], "MODERATOR_ROLE -> acct 6");
        _grantIfMissing(covertProtocol, MODERATOR_ROLE, accounts[9], "MODERATOR_ROLE -> acct 9");

        vm.stopBroadcast();

        console.log("\n==========================================");
        console.log("Reset complete. All accounts have 30 COV.");
        console.log("==========================================");
    }

    function _grantIfMissing(
        CovertProtocol proto,
        bytes32 role,
        address acct,
        string memory label
    ) internal {
        if (!proto.hasRole(role, acct)) {
            proto.grantRole(role, acct);
            console.log("Granted", label);
        } else {
            console.log("Already has", label);
        }
    }
}
