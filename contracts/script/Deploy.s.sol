// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/CommitmentRegistry.sol";
import "../src/DailyAnchor.sol";

/**
 * @title DeployScript
 * @notice Deploys C.O.V.E.R.T contracts to multiple networks
 * @dev Usage:
 *   Local:    forge script script/Deploy.s.sol --rpc-url localhost --broadcast
 *   Testnet:  forge script script/Deploy.s.sol --rpc-url $BASE_SEPOLIA_RPC_URL --broadcast --verify
 *   Mainnet:  forge script script/Deploy.s.sol --rpc-url $BASE_RPC_URL --broadcast --verify
 */
contract DeployScript is Script {
    // Deployment configuration
    struct DeploymentConfig {
        address deployer;
        uint256 chainId;
        string networkName;
    }

    // Deployed contract addresses
    CommitmentRegistry public commitmentRegistry;
    DailyAnchor public dailyAnchor;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);

        DeploymentConfig memory config = getConfig();

        console.log("===========================================");
        console.log("C.O.V.E.R.T Contract Deployment");
        console.log("===========================================");
        console.log("Network:", config.networkName);
        console.log("Chain ID:", config.chainId);
        console.log("Deployer:", deployer);
        console.log("Deployer Balance:", deployer.balance);
        console.log("===========================================");

        vm.startBroadcast(deployerPrivateKey);

        // Deploy CommitmentRegistry
        console.log("\nDeploying CommitmentRegistry...");
        commitmentRegistry = new CommitmentRegistry();
        console.log("CommitmentRegistry deployed at:", address(commitmentRegistry));

        // Deploy DailyAnchor
        console.log("\nDeploying DailyAnchor...");
        dailyAnchor = new DailyAnchor();
        console.log("DailyAnchor deployed at:", address(dailyAnchor));

        vm.stopBroadcast();

        // Post-deployment configuration
        postDeploymentSetup(deployer);

        // Save deployment addresses
        saveDeployment(config);

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

    function postDeploymentSetup(address deployer) internal view {
        console.log("\n--- Post-Deployment Configuration ---");

        // Verify CommitmentRegistry is properly initialized
        console.log("CommitmentRegistry owner:", deployer);

        // Verify DailyAnchor is properly initialized
        console.log("DailyAnchor owner:", dailyAnchor.owner());
        console.log("DailyAnchor deployer is operator:", dailyAnchor.operators(deployer));
    }

    function saveDeployment(DeploymentConfig memory config) internal {
        string memory deploymentDir = "deployments";

        // Create deployment info
        string memory json = string.concat(
            "{\n",
            '  "network": "',
            config.networkName,
            '",\n',
            '  "chainId": ',
            vm.toString(config.chainId),
            ",\n",
            '  "deployer": "',
            vm.toString(config.deployer),
            '",\n',
            '  "contracts": {\n',
            '    "CommitmentRegistry": "',
            vm.toString(address(commitmentRegistry)),
            '",\n',
            '    "DailyAnchor": "',
            vm.toString(address(dailyAnchor)),
            '"\n',
            "  },\n",
            '  "timestamp": ',
            vm.toString(block.timestamp),
            "\n",
            "}"
        );

        // Save to network-specific file
        string memory filename = string.concat(deploymentDir, "/", config.networkName, ".json");
        vm.writeFile(filename, json);
        console.log("\nDeployment saved to:", filename);

        // Also save to latest.json
        string memory latestFilename = string.concat(deploymentDir, "/latest.json");
        vm.writeFile(latestFilename, json);

        // Save env format for easy sourcing
        string memory envContent = string.concat(
            "# C.O.V.E.R.T Contract Addresses - ",
            config.networkName,
            "\n",
            "COMMITMENT_REGISTRY_ADDRESS=",
            vm.toString(address(commitmentRegistry)),
            "\n",
            "DAILY_ANCHOR_ADDRESS=",
            vm.toString(address(dailyAnchor)),
            "\n"
        );

        string memory envFilename = string.concat(deploymentDir, "/", config.networkName, ".env");
        vm.writeFile(envFilename, envContent);
        console.log("Env file saved to:", envFilename);
    }
}

/**
 * @title DeployLocalScript
 * @notice Quick deployment for local development
 */
contract DeployLocalScript is Script {
    function run() external {
        // Use default anvil key
        uint256 deployerPrivateKey = 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80;

        vm.startBroadcast(deployerPrivateKey);

        CommitmentRegistry registry = new CommitmentRegistry();
        console.log("CommitmentRegistry:", address(registry));

        DailyAnchor anchor = new DailyAnchor();
        console.log("DailyAnchor:", address(anchor));

        vm.stopBroadcast();

        // Write to deployments
        string memory content = string.concat(
            "COMMITMENT_REGISTRY_ADDRESS=",
            vm.toString(address(registry)),
            "\nDAILY_ANCHOR_ADDRESS=",
            vm.toString(address(anchor))
        );
        vm.writeFile("deployments/localhost.env", content);
    }
}
