// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/DailyAnchor.sol";

contract DailyAnchorTest is Test {
    DailyAnchor public anchor;

    address public owner = address(this);
    address public operator1 = address(0x1);
    address public operator2 = address(0x2);
    address public unauthorized = address(0x666);

    uint256 public testDate1 = 20241115;
    uint256 public testDate2 = 20241116;
    bytes32 public testRoot1 = keccak256("merkleroot1");
    bytes32 public testRoot2 = keccak256("merkleroot2");

    event AnchorSubmitted(uint256 indexed date, bytes32 merkleRoot, uint256 actionCount, address operator);
    event OperatorAdded(address indexed operator);
    event OperatorRemoved(address indexed operator);

    function setUp() public {
        anchor = new DailyAnchor();
    }

    // ============ Deployment Tests ============

    function test_OwnerIsDeployer() public {
        assertEq(anchor.owner(), address(this));
    }

    function test_DeployerIsOperator() public {
        assertTrue(anchor.operators(address(this)));
    }

    // ============ Anchor Submission Tests ============

    function test_SubmitAnchor() public {
        anchor.submitAnchor(testDate1, testRoot1, 100);

        DailyAnchor.Anchor memory a = anchor.getAnchor(testDate1);

        assertEq(a.merkleRoot, testRoot1);
        assertEq(a.actionCount, 100);
        assertEq(a.operator, address(this));
        assertEq(a.timestamp, block.timestamp);
    }

    function test_SubmitMultipleAnchors() public {
        anchor.submitAnchor(testDate1, testRoot1, 100);
        anchor.submitAnchor(testDate2, testRoot2, 200);

        DailyAnchor.Anchor memory a1 = anchor.getAnchor(testDate1);
        DailyAnchor.Anchor memory a2 = anchor.getAnchor(testDate2);

        assertEq(a1.merkleRoot, testRoot1);
        assertEq(a2.merkleRoot, testRoot2);
        assertEq(a1.actionCount, 100);
        assertEq(a2.actionCount, 200);
    }

    function test_SubmitAnchorByAuthorizedOperator() public {
        anchor.addOperator(operator1);

        vm.prank(operator1);
        anchor.submitAnchor(testDate1, testRoot1, 50);

        DailyAnchor.Anchor memory a = anchor.getAnchor(testDate1);
        assertEq(a.operator, operator1);
    }

    function test_SubmitAnchorEmitsEvent() public {
        vm.expectEmit(true, false, false, true);
        emit AnchorSubmitted(testDate1, testRoot1, 100, address(this));

        anchor.submitAnchor(testDate1, testRoot1, 100);
    }

    // ============ Revert Tests ============

    function test_RevertUnauthorizedSubmit() public {
        vm.prank(unauthorized);
        vm.expectRevert(DailyAnchor.UnauthorizedOperator.selector);
        anchor.submitAnchor(testDate1, testRoot1, 100);
    }

    function test_RevertDuplicateAnchor() public {
        anchor.submitAnchor(testDate1, testRoot1, 100);

        vm.expectRevert(DailyAnchor.AnchorAlreadyExists.selector);
        anchor.submitAnchor(testDate1, testRoot2, 200);
    }

    function test_RevertDuplicateAnchorFromDifferentOperator() public {
        anchor.addOperator(operator1);

        anchor.submitAnchor(testDate1, testRoot1, 100);

        vm.prank(operator1);
        vm.expectRevert(DailyAnchor.AnchorAlreadyExists.selector);
        anchor.submitAnchor(testDate1, testRoot2, 200);
    }

    // ============ Operator Management Tests ============

    function test_AddOperator() public {
        assertFalse(anchor.operators(operator1));

        anchor.addOperator(operator1);

        assertTrue(anchor.operators(operator1));
    }

    function test_AddOperatorEmitsEvent() public {
        vm.expectEmit(true, false, false, false);
        emit OperatorAdded(operator1);

        anchor.addOperator(operator1);
    }

    function test_RemoveOperator() public {
        anchor.addOperator(operator1);
        assertTrue(anchor.operators(operator1));

        anchor.removeOperator(operator1);

        assertFalse(anchor.operators(operator1));
    }

    function test_RemoveOperatorEmitsEvent() public {
        anchor.addOperator(operator1);

        vm.expectEmit(true, false, false, false);
        emit OperatorRemoved(operator1);

        anchor.removeOperator(operator1);
    }

    function test_RevertNonOwnerAddOperator() public {
        vm.prank(unauthorized);
        vm.expectRevert(DailyAnchor.OnlyOwner.selector);
        anchor.addOperator(operator1);
    }

    function test_RevertNonOwnerRemoveOperator() public {
        anchor.addOperator(operator1);

        vm.prank(unauthorized);
        vm.expectRevert(DailyAnchor.OnlyOwner.selector);
        anchor.removeOperator(operator1);
    }

    function test_RemovedOperatorCannotSubmit() public {
        anchor.addOperator(operator1);

        vm.prank(operator1);
        anchor.submitAnchor(testDate1, testRoot1, 100);

        anchor.removeOperator(operator1);

        vm.prank(operator1);
        vm.expectRevert(DailyAnchor.UnauthorizedOperator.selector);
        anchor.submitAnchor(testDate2, testRoot2, 200);
    }

    // ============ Merkle Proof Verification Tests ============

    function test_VerifyProofSingleLeaf() public {
        // Single leaf tree - root is the leaf
        bytes32 leaf = keccak256("action1");
        bytes32[] memory proof = new bytes32[](0);

        anchor.submitAnchor(testDate1, leaf, 1);

        assertTrue(anchor.verifyProof(testDate1, proof, leaf));
    }

    function test_VerifyProofTwoLeaves() public {
        // Two leaf tree
        bytes32 leaf1 = keccak256("action1");
        bytes32 leaf2 = keccak256("action2");

        bytes32 root;
        if (leaf1 <= leaf2) {
            root = keccak256(abi.encodePacked(leaf1, leaf2));
        } else {
            root = keccak256(abi.encodePacked(leaf2, leaf1));
        }

        anchor.submitAnchor(testDate1, root, 2);

        // Proof for leaf1
        bytes32[] memory proof = new bytes32[](1);
        proof[0] = leaf2;

        assertTrue(anchor.verifyProof(testDate1, proof, leaf1));
    }

    function test_VerifyProofFourLeaves() public {
        bytes32 leaf1 = keccak256("a1");
        bytes32 leaf2 = keccak256("a2");
        bytes32 leaf3 = keccak256("a3");
        bytes32 leaf4 = keccak256("a4");

        // Build tree
        bytes32 node1 = leaf1 <= leaf2
            ? keccak256(abi.encodePacked(leaf1, leaf2))
            : keccak256(abi.encodePacked(leaf2, leaf1));
        bytes32 node2 = leaf3 <= leaf4
            ? keccak256(abi.encodePacked(leaf3, leaf4))
            : keccak256(abi.encodePacked(leaf4, leaf3));
        bytes32 root = node1 <= node2
            ? keccak256(abi.encodePacked(node1, node2))
            : keccak256(abi.encodePacked(node2, node1));

        anchor.submitAnchor(testDate1, root, 4);

        // Proof for leaf1: [leaf2, node2]
        bytes32[] memory proof = new bytes32[](2);
        proof[0] = leaf2;
        proof[1] = node2;

        assertTrue(anchor.verifyProof(testDate1, proof, leaf1));
    }

    function test_InvalidProofFails() public {
        bytes32 leaf = keccak256("action1");
        bytes32 fakeLeaf = keccak256("fake");
        bytes32[] memory proof = new bytes32[](0);

        anchor.submitAnchor(testDate1, leaf, 1);

        assertFalse(anchor.verifyProof(testDate1, proof, fakeLeaf));
    }

    function test_VerifyProofNonExistentDate() public {
        bytes32 leaf = keccak256("action1");
        bytes32[] memory proof = new bytes32[](0);

        // No anchor for this date
        assertFalse(anchor.verifyProof(testDate1, proof, leaf));
    }

    // ============ View Function Tests ============

    function test_GetAnchorReturnsCorrectData() public {
        vm.warp(12345678);
        anchor.submitAnchor(testDate1, testRoot1, 42);

        DailyAnchor.Anchor memory a = anchor.getAnchor(testDate1);

        assertEq(a.merkleRoot, testRoot1);
        assertEq(a.actionCount, 42);
        assertEq(a.timestamp, 12345678);
        assertEq(a.operator, address(this));
    }

    function test_GetAnchorNonExistent() public {
        DailyAnchor.Anchor memory a = anchor.getAnchor(testDate1);

        assertEq(a.merkleRoot, bytes32(0));
        assertEq(a.actionCount, 0);
        assertEq(a.timestamp, 0);
    }

    // ============ Edge Case Tests ============

    function test_AnchorWithZeroActionCount() public {
        // Edge case: no actions but still anchoring
        // Contract should allow this (maybe for empty day)
        anchor.submitAnchor(testDate1, testRoot1, 0);

        DailyAnchor.Anchor memory a = anchor.getAnchor(testDate1);
        assertEq(a.actionCount, 0);
    }

    function test_AnchorWithLargeActionCount() public {
        uint256 largeCount = type(uint256).max;
        anchor.submitAnchor(testDate1, testRoot1, largeCount);

        DailyAnchor.Anchor memory a = anchor.getAnchor(testDate1);
        assertEq(a.actionCount, largeCount);
    }

    // ============ Fuzz Tests ============

    function testFuzz_SubmitAnchorWithAnyDate(uint256 date) public {
        anchor.submitAnchor(date, testRoot1, 100);

        DailyAnchor.Anchor memory a = anchor.getAnchor(date);
        assertEq(a.merkleRoot, testRoot1);
    }

    function testFuzz_SubmitAnchorWithAnyRoot(bytes32 root) public {
        anchor.submitAnchor(testDate1, root, 100);

        DailyAnchor.Anchor memory a = anchor.getAnchor(testDate1);
        assertEq(a.merkleRoot, root);
    }

    function testFuzz_SubmitAnchorWithAnyActionCount(uint256 count) public {
        anchor.submitAnchor(testDate1, testRoot1, count);

        DailyAnchor.Anchor memory a = anchor.getAnchor(testDate1);
        assertEq(a.actionCount, count);
    }

    // ============ Gas Tests ============

    function test_GasCostSubmitAnchor() public {
        uint256 gasBefore = gasleft();
        anchor.submitAnchor(testDate1, testRoot1, 100);
        uint256 gasAfter = gasleft();

        uint256 gasUsed = gasBefore - gasAfter;
        console.log("Gas used for submitAnchor:", gasUsed);

        assertLt(gasUsed, 110000);
    }

    function test_GasCostVerifyProof() public {
        bytes32 leaf = keccak256("action1");
        bytes32[] memory proof = new bytes32[](0);

        anchor.submitAnchor(testDate1, leaf, 1);

        uint256 gasBefore = gasleft();
        anchor.verifyProof(testDate1, proof, leaf);
        uint256 gasAfter = gasleft();

        uint256 gasUsed = gasBefore - gasAfter;
        console.log("Gas used for verifyProof (depth 0):", gasUsed);

        assertLt(gasUsed, 10000);
    }

    function test_GasCostAddOperator() public {
        uint256 gasBefore = gasleft();
        anchor.addOperator(operator1);
        uint256 gasAfter = gasleft();

        uint256 gasUsed = gasBefore - gasAfter;
        console.log("Gas used for addOperator:", gasUsed);

        assertLt(gasUsed, 50000);
    }
}
