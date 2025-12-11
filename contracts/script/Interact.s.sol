// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/CommitmentRegistry.sol";
import "../src/DailyAnchor.sol";

/**
 * @title InteractScript
 * @notice Examples for interacting with deployed C.O.V.E.R.T contracts
 */
contract InteractScript is Script {
    CommitmentRegistry public registry;
    DailyAnchor public anchor;

    function setUp() public {
        // Load deployed addresses from environment
        address registryAddr = vm.envAddress("COMMITMENT_REGISTRY_ADDRESS");
        address anchorAddr = vm.envAddress("DAILY_ANCHOR_ADDRESS");

        registry = CommitmentRegistry(registryAddr);
        anchor = DailyAnchor(anchorAddr);
    }

    function run() external view {
        console.log("===========================================");
        console.log("C.O.V.E.R.T Contract Interaction Examples");
        console.log("===========================================");
        console.log("CommitmentRegistry:", address(registry));
        console.log("DailyAnchor:", address(anchor));
        console.log("===========================================");
    }
}

/**
 * @title CommitReportScript
 * @notice Submit a new report commitment
 * @dev Usage: forge script script/Interact.s.sol:CommitReportScript --rpc-url localhost --broadcast
 */
contract CommitReportScript is Script {
    function run() external {
        uint256 privateKey = vm.envUint("PRIVATE_KEY");
        address registryAddr = vm.envAddress("COMMITMENT_REGISTRY_ADDRESS");

        CommitmentRegistry registry = CommitmentRegistry(registryAddr);

        // Example CID hash (would be computed from actual IPFS CID)
        bytes32 cidHash = keccak256(abi.encodePacked("bafyexamplecid", block.timestamp));
        uint8 visibility = 1; // moderated

        console.log("Submitting report commitment...");
        console.log("CID Hash:", vm.toString(cidHash));
        console.log("Visibility:", visibility);

        vm.startBroadcast(privateKey);

        registry.commit(cidHash, visibility);

        vm.stopBroadcast();

        console.log("Report committed successfully!");

        // Verify
        CommitmentRegistry.Commitment memory c = registry.getCommitment(cidHash);
        console.log("Verified - Submitter:", c.submitter);
        console.log("Verified - Timestamp:", c.timestamp);
    }
}

/**
 * @title VerifyCommitmentScript
 * @notice Verify an existing commitment
 */
contract VerifyCommitmentScript is Script {
    function run() external view {
        address registryAddr = vm.envAddress("COMMITMENT_REGISTRY_ADDRESS");
        bytes32 cidHash = vm.envBytes32("CID_HASH");

        CommitmentRegistry registry = CommitmentRegistry(registryAddr);

        bool isValid = registry.isActive(cidHash);

        console.log("Commitment Verification");
        console.log("CID Hash:", vm.toString(cidHash));
        console.log("Is Active:", isValid);

        if (isValid) {
            CommitmentRegistry.Commitment memory c = registry.getCommitment(cidHash);
            console.log("Submitter:", c.submitter);
            console.log("Visibility:", c.visibility);
            console.log("Timestamp:", c.timestamp);
        }
    }
}

/**
 * @title SubmitAnchorScript
 * @notice Submit a daily anchor
 */
contract SubmitAnchorScript is Script {
    function run() external {
        uint256 privateKey = vm.envUint("PRIVATE_KEY");
        address anchorAddr = vm.envAddress("DAILY_ANCHOR_ADDRESS");

        DailyAnchor anchor = DailyAnchor(anchorAddr);

        // Example: Today's date as YYYYMMDD
        uint256 date = 20241119;
        bytes32 merkleRoot = keccak256(abi.encodePacked("example_merkle_root"));
        uint256 actionCount = 42;

        console.log("Submitting daily anchor...");
        console.log("Date:", date);
        console.log("Merkle Root:", vm.toString(merkleRoot));
        console.log("Action Count:", actionCount);

        vm.startBroadcast(privateKey);

        anchor.submitAnchor(date, merkleRoot, actionCount);

        vm.stopBroadcast();

        console.log("Anchor submitted successfully!");
    }
}

/**
 * @title AddOperatorScript
 * @notice Add an operator to DailyAnchor
 */
contract AddOperatorScript is Script {
    function run() external {
        uint256 privateKey = vm.envUint("PRIVATE_KEY");
        address anchorAddr = vm.envAddress("DAILY_ANCHOR_ADDRESS");
        address newOperator = vm.envAddress("NEW_OPERATOR");

        DailyAnchor anchor = DailyAnchor(anchorAddr);

        console.log("Adding operator...");
        console.log("New Operator:", newOperator);

        vm.startBroadcast(privateKey);

        anchor.addOperator(newOperator);

        vm.stopBroadcast();

        console.log("Operator added successfully!");
        console.log("Is Operator:", anchor.operators(newOperator));
    }
}

/**
 * @title DeactivateReportScript
 * @notice Deactivate a report commitment
 */
contract DeactivateReportScript is Script {
    function run() external {
        uint256 privateKey = vm.envUint("PRIVATE_KEY");
        address registryAddr = vm.envAddress("COMMITMENT_REGISTRY_ADDRESS");
        bytes32 cidHash = vm.envBytes32("CID_HASH");

        CommitmentRegistry registry = CommitmentRegistry(registryAddr);

        console.log("Deactivating report...");
        console.log("CID Hash:", vm.toString(cidHash));

        vm.startBroadcast(privateKey);

        registry.deactivate(cidHash);

        vm.stopBroadcast();

        console.log("Report deactivated!");
        console.log("Is Active:", registry.isActive(cidHash));
    }
}

/**
 * @title BatchCommitScript
 * @notice Example of submitting multiple commitments
 */
contract BatchCommitScript is Script {
    function run() external {
        uint256 privateKey = vm.envUint("PRIVATE_KEY");
        address registryAddr = vm.envAddress("COMMITMENT_REGISTRY_ADDRESS");

        CommitmentRegistry registry = CommitmentRegistry(registryAddr);

        // Generate multiple CID hashes
        uint256 count = 3;
        bytes32[] memory cidHashes = new bytes32[](count);
        uint8[] memory visibilities = new uint8[](count);

        for (uint256 i = 0; i < count; i++) {
            cidHashes[i] = keccak256(abi.encodePacked("batch_cid_", i, block.timestamp));
            visibilities[i] = uint8(i % 3); // 0, 1, 2
        }

        console.log("Batch committing", count, "reports...");

        vm.startBroadcast(privateKey);

        // Note: The current contract doesn't have batch commit, so we loop
        for (uint256 i = 0; i < count; i++) {
            registry.commit(cidHashes[i], visibilities[i]);
            console.log("Committed:", vm.toString(cidHashes[i]));
        }

        vm.stopBroadcast();

        console.log("Batch commit complete!");
    }
}
