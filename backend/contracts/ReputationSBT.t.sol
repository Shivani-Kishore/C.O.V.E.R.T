// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "./ReputationSBT.sol";

contract ReputationSBTTest is Test {
    ReputationSBT public reputation;
    address public admin;
    address public manager;
    address public user1;
    address public user2;

    function setUp() public {
        admin = address(this);
        manager = address(0x1);
        user1 = address(0x2);
        user2 = address(0x3);

        reputation = new ReputationSBT("https://api.covert.dev/metadata/");

        reputation.grantRole(reputation.MANAGER_ROLE(), manager);
    }

    function testMintReputation() public {
        uint256 tokenId = reputation.mint(user1, 0);

        assertEq(tokenId, 1);
        assertEq(reputation.ownerOf(tokenId), user1);
        assertEq(reputation.walletToToken(user1), tokenId);

        ReputationSBT.ReputationData memory rep = reputation.getReputation(tokenId);
        assertEq(rep.score, 0);
        assertEq(uint256(rep.tier), uint256(ReputationSBT.Tier.BRONZE));
        assertTrue(rep.isActive);
    }

    function testCannotMintToSameAddressTwice() public {
        reputation.mint(user1, 0);

        vm.expectRevert("Address already has reputation token");
        reputation.mint(user1, 0);
    }

    function testTierCalculation() public {
        uint256 tokenId1 = reputation.mint(user1, 0);
        ReputationSBT.ReputationData memory rep1 = reputation.getReputation(tokenId1);
        assertEq(uint256(rep1.tier), uint256(ReputationSBT.Tier.BRONZE));

        uint256 tokenId2 = reputation.mint(user2, 150);
        ReputationSBT.ReputationData memory rep2 = reputation.getReputation(tokenId2);
        assertEq(uint256(rep2.tier), uint256(ReputationSBT.Tier.SILVER));
    }

    function testUpdateReputationAccurate() public {
        uint256 tokenId = reputation.mint(user1, 0);

        vm.prank(manager);
        reputation.updateReputation(tokenId, true, false);

        ReputationSBT.ReputationData memory rep = reputation.getReputation(tokenId);
        assertEq(rep.score, 10);
        assertEq(rep.totalReviews, 1);
        assertEq(rep.accurateReviews, 1);
    }

    function testUpdateReputationDisputed() public {
        uint256 tokenId = reputation.mint(user1, 50);

        vm.prank(manager);
        reputation.updateReputation(tokenId, false, true);

        ReputationSBT.ReputationData memory rep = reputation.getReputation(tokenId);
        assertEq(rep.score, 30);
        assertEq(rep.disputedReviews, 1);
    }

    function testTierUpgrade() public {
        uint256 tokenId = reputation.mint(user1, 90);

        ReputationSBT.ReputationData memory repBefore = reputation.getReputation(tokenId);
        assertEq(uint256(repBefore.tier), uint256(ReputationSBT.Tier.BRONZE));

        vm.prank(manager);
        reputation.updateReputation(tokenId, true, false);

        ReputationSBT.ReputationData memory repAfter = reputation.getReputation(tokenId);
        assertEq(repAfter.score, 100);
        assertEq(uint256(repAfter.tier), uint256(ReputationSBT.Tier.SILVER));
    }

    function testReputationDecay() public {
        uint256 tokenId = reputation.mint(user1, 100);

        vm.warp(block.timestamp + 7 days);

        reputation.applyDecay(tokenId);

        ReputationSBT.ReputationData memory rep = reputation.getReputation(tokenId);
        assertEq(rep.score, 99);
    }

    function testMultiPeriodDecay() public {
        uint256 tokenId = reputation.mint(user1, 100);

        vm.warp(block.timestamp + 21 days);

        reputation.applyDecay(tokenId);

        ReputationSBT.ReputationData memory rep = reputation.getReputation(tokenId);
        assertEq(rep.score, 97);
    }

    function testRevokeReputation() public {
        uint256 tokenId = reputation.mint(user1, 100);

        vm.prank(manager);
        reputation.revokeReputation(tokenId);

        ReputationSBT.ReputationData memory rep = reputation.getReputation(tokenId);
        assertFalse(rep.isActive);
    }

    function testCannotUpdateRevokedReputation() public {
        uint256 tokenId = reputation.mint(user1, 100);

        vm.prank(manager);
        reputation.revokeReputation(tokenId);

        vm.prank(manager);
        vm.expectRevert("Reputation is not active");
        reputation.updateReputation(tokenId, true, false);
    }

    function testAccuracyRate() public {
        uint256 tokenId = reputation.mint(user1, 0);

        vm.startPrank(manager);
        reputation.updateReputation(tokenId, true, false);
        reputation.updateReputation(tokenId, true, false);
        reputation.updateReputation(tokenId, false, false);
        reputation.updateReputation(tokenId, true, false);
        vm.stopPrank();

        uint256 accuracy = reputation.getAccuracyRate(tokenId);
        assertEq(accuracy, 75);
    }

    function testSoulBoundTransferRestriction() public {
        uint256 tokenId = reputation.mint(user1, 0);

        vm.prank(user1);
        vm.expectRevert("Soul-bound: Transfer not allowed");
        reputation.transferFrom(user1, user2, tokenId);
    }

    function testGetWalletReputation() public {
        uint256 tokenId = reputation.mint(user1, 150);

        ReputationSBT.ReputationData memory rep = reputation.getWalletReputation(user1);
        assertEq(rep.score, 150);
        assertEq(uint256(rep.tier), uint256(ReputationSBT.Tier.SILVER));
    }

    function testTokenURI() public {
        uint256 tokenId = reputation.mint(user1, 150);

        string memory uri = reputation.tokenURI(tokenId);

        assertTrue(bytes(uri).length > 0);
    }

    function testOnlyManagerCanUpdateReputation() public {
        uint256 tokenId = reputation.mint(user1, 0);

        vm.prank(user2);
        vm.expectRevert();
        reputation.updateReputation(tokenId, true, false);
    }

    function testOnlyMinterCanMint() public {
        vm.prank(user1);
        vm.expectRevert();
        reputation.mint(user2, 0);
    }
}
