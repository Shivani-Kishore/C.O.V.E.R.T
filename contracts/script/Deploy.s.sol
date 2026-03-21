// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/CommitmentRegistry.sol";
import "../src/DailyAnchor.sol";
import "../src/COVCredits.sol";
import "../src/CovertBadges.sol";
import "../src/CovertProtocol.sol";

/**
 * @title DeployScript
 * @notice Deploys all C.O.V.E.R.T contracts and wires roles.
 * @dev Usage:
 *   Local:    forge script script/Deploy.s.sol --rpc-url localhost --broadcast
 *   Testnet:  forge script script/Deploy.s.sol --rpc-url $BASE_SEPOLIA_RPC_URL --broadcast --verify
 *   Mainnet:  forge script script/Deploy.s.sol --rpc-url $BASE_RPC_URL --broadcast --verify
 */
contract DeployScript is Script {
    struct DeploymentConfig {
        address deployer;
        uint256 chainId;
        string networkName;
    }

    // Legacy contracts
    CommitmentRegistry public commitmentRegistry;
    DailyAnchor public dailyAnchor;

    // New protocol contracts
    COVCredits public covCredits;
    CovertBadges public covBadges;
    CovertProtocol public covertProtocol;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        address treasury = vm.envOr("TREASURY_ADDRESS", deployer);
        address automationWallet = vm.envOr("AUTOMATION_WALLET", deployer);

        DeploymentConfig memory config = getConfig();

        console.log("===========================================");
        console.log("C.O.V.E.R.T Contract Deployment (v2)");
        console.log("===========================================");
        console.log("Network:", config.networkName);
        console.log("Chain ID:", config.chainId);
        console.log("Deployer:", deployer);
        console.log("Treasury:", treasury);
        console.log("Automation Wallet:", automationWallet);
        console.log("Deployer Balance:", deployer.balance);
        console.log("===========================================");

        vm.startBroadcast(deployerPrivateKey);

        // ── 1. Deploy Legacy Contracts ──
        console.log("\nDeploying CommitmentRegistry...");
        commitmentRegistry = new CommitmentRegistry();
        console.log("CommitmentRegistry deployed at:", address(commitmentRegistry));

        console.log("\nDeploying DailyAnchor...");
        dailyAnchor = new DailyAnchor();
        console.log("DailyAnchor deployed at:", address(dailyAnchor));

        // ── 2. Deploy COVCredits ──
        console.log("\nDeploying COVCredits...");
        covCredits = new COVCredits(deployer);
        console.log("COVCredits deployed at:", address(covCredits));

        // ── 3. Deploy CovertBadges ──
        console.log("\nDeploying CovertBadges...");
        covBadges = new CovertBadges(deployer);
        console.log("CovertBadges deployed at:", address(covBadges));

        // ── 4. Deploy CovertProtocol ──
        console.log("\nDeploying CovertProtocol...");
        covertProtocol = new CovertProtocol(deployer, treasury, address(covCredits), address(covBadges));
        console.log("CovertProtocol deployed at:", address(covertProtocol));

        // ── 5. Wire up roles ──
        console.log("\n--- Wiring Roles ---");

        // Grant protocol MINTER + BURNER on COVCredits
        covCredits.grantRole(covCredits.MINTER_ROLE(), address(covertProtocol));
        console.log("Granted MINTER_ROLE to CovertProtocol");
        covCredits.grantRole(covCredits.BURNER_ROLE(), address(covertProtocol));
        console.log("Granted BURNER_ROLE to CovertProtocol");

        // Grant automation wallet BADGE_MANAGER_ROLE on CovertBadges
        if (automationWallet != deployer) {
            covBadges.grantRole(covBadges.BADGE_MANAGER_ROLE(), automationWallet);
            console.log("Granted BADGE_MANAGER_ROLE to automation wallet");
        }

        // Grant automation wallet AUTOMATION_ROLE on CovertProtocol
        if (automationWallet != deployer) {
            covertProtocol.grantRole(covertProtocol.AUTOMATION_ROLE(), automationWallet);
            console.log("Granted AUTOMATION_ROLE to automation wallet");
        }

        vm.stopBroadcast();

        // Save deployment
        saveDeployment(config, treasury, automationWallet);

        console.log("\n===========================================");
        console.log("Deployment Complete!");
        console.log("===========================================");
    }

    function getConfig() internal view returns (DeploymentConfig memory) {
        uint256 chainId = block.chainid;
        string memory networkName;

        if (chainId == 31337) {
            networkName = "localhost";
        } else if (chainId == 84532) {
            networkName = "base-sepolia";
        } else if (chainId == 8453) {
            networkName = "base-mainnet";
        } else if (chainId == 11155111) {
            networkName = "sepolia";
        } else if (chainId == 1) {
            networkName = "mainnet";
        } else if (chainId == 137) {
            networkName = "polygon";
        } else if (chainId == 80001) {
            networkName = "polygon-mumbai";
        } else {
            networkName = "unknown";
        }

        return DeploymentConfig({deployer: msg.sender, chainId: chainId, networkName: networkName});
    }

    function saveDeployment(DeploymentConfig memory config, address treasury, address automationWallet) internal {
        string memory deploymentDir = "deployments";

        string memory json = string.concat(
            "{\n",
            '  "network": "', config.networkName, '",\n',
            '  "chainId": ', vm.toString(config.chainId), ",\n",
            '  "deployer": "', vm.toString(config.deployer), '",\n',
            '  "treasury": "', vm.toString(treasury), '",\n',
            '  "automationWallet": "', vm.toString(automationWallet), '",\n',
            '  "contracts": {\n',
            '    "CommitmentRegistry": "', vm.toString(address(commitmentRegistry)), '",\n',
            '    "DailyAnchor": "', vm.toString(address(dailyAnchor)), '",\n',
            '    "COVCredits": "', vm.toString(address(covCredits)), '",\n',
            '    "CovertBadges": "', vm.toString(address(covBadges)), '",\n',
            '    "CovertProtocol": "', vm.toString(address(covertProtocol)), '"\n',
            "  },\n",
            '  "timestamp": ', vm.toString(block.timestamp), "\n",
            "}"
        );

        string memory filename = string.concat(deploymentDir, "/", config.networkName, ".json");
        vm.writeFile(filename, json);
        console.log("\nDeployment saved to:", filename);

        string memory latestFilename = string.concat(deploymentDir, "/latest.json");
        vm.writeFile(latestFilename, json);

        string memory envContent = string.concat(
            "# C.O.V.E.R.T Contract Addresses - ", config.networkName, "\n",
            "COMMITMENT_REGISTRY_ADDRESS=", vm.toString(address(commitmentRegistry)), "\n",
            "DAILY_ANCHOR_ADDRESS=", vm.toString(address(dailyAnchor)), "\n",
            "COV_CREDITS_ADDRESS=", vm.toString(address(covCredits)), "\n",
            "COVERT_BADGES_ADDRESS=", vm.toString(address(covBadges)), "\n",
            "COVERT_PROTOCOL_ADDRESS=", vm.toString(address(covertProtocol)), "\n"
        );

        string memory envFilename = string.concat(deploymentDir, "/", config.networkName, ".env");
        vm.writeFile(envFilename, envContent);
        console.log("Env file saved to:", envFilename);
    }
}

/**
 * @title DeployLocalScript
 * @notice Quick deployment for local development (Anvil).
 */
contract DeployLocalScript is Script {
    function run() external {
        // Default to Anvil account #0; override with PRIVATE_KEY env var for real deployments
        uint256 deployerPrivateKey = vm.envOr("PRIVATE_KEY", uint256(0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80));
        address deployer = vm.addr(deployerPrivateKey);

        vm.startBroadcast(deployerPrivateKey);

        // Legacy
        CommitmentRegistry registry = new CommitmentRegistry();
        console.log("CommitmentRegistry:", address(registry));

        DailyAnchor anchor = new DailyAnchor();
        console.log("DailyAnchor:", address(anchor));

        // New protocol
        COVCredits credits = new COVCredits(deployer);
        console.log("COVCredits:", address(credits));

        CovertBadges badges = new CovertBadges(deployer);
        console.log("CovertBadges:", address(badges));

        CovertProtocol protocol = new CovertProtocol(deployer, deployer, address(credits), address(badges));
        console.log("CovertProtocol:", address(protocol));

        // Wire roles
        credits.grantRole(credits.MINTER_ROLE(), address(protocol));
        credits.grantRole(credits.BURNER_ROLE(), address(protocol));

        vm.stopBroadcast();

        // Write deployment env
        string memory content = string.concat(
            "COMMITMENT_REGISTRY_ADDRESS=", vm.toString(address(registry)),
            "\nDAILY_ANCHOR_ADDRESS=", vm.toString(address(anchor)),
            "\nCOV_CREDITS_ADDRESS=", vm.toString(address(credits)),
            "\nCOVERT_BADGES_ADDRESS=", vm.toString(address(badges)),
            "\nCOVERT_PROTOCOL_ADDRESS=", vm.toString(address(protocol))
        );
        vm.writeFile("deployments/localhost.env", content);
    }
}
