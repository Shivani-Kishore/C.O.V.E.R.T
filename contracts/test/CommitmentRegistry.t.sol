// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/CommitmentRegistry.sol";

contract CommitmentRegistryTest is Test {
    CommitmentRegistry public registry;

    address public reporter1 = address(0x1);
    address public reporter2 = address(0x2);
    address public attacker = address(0x666);

    bytes32 public testCidHash1 = keccak256("bafytest123");
    bytes32 public testCidHash2 = keccak256("bafytest456");
    bytes32 public testCidHash3 = keccak256("bafytest789");

    event ReportCommitted(bytes32 indexed cidHash, address indexed submitter, uint8 visibility, uint256 timestamp);
    event ReportDeactivated(bytes32 indexed cidHash, address indexed submitter);

    function setUp() public {
        registry = new CommitmentRegistry();
    }

    // ============ Core Functionality Tests ============

    function test_CommitReport() public {
        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        CommitmentRegistry.Commitment memory commitment = registry.getCommitment(testCidHash1);

        assertEq(commitment.cidHash, testCidHash1);
        assertEq(commitment.submitter, reporter1);
        assertEq(commitment.visibility, 1);
        assertTrue(commitment.isActive);
        assertEq(commitment.timestamp, block.timestamp);
    }

    function test_CommitWithDifferentVisibilities() public {
        // Private (0)
        vm.prank(reporter1);
        registry.commit(testCidHash1, 0);
        assertEq(registry.getCommitment(testCidHash1).visibility, 0);

        // Moderated (1)
        vm.prank(reporter1);
        registry.commit(testCidHash2, 1);
        assertEq(registry.getCommitment(testCidHash2).visibility, 1);

        // Public (2)
        vm.prank(reporter1);
        registry.commit(testCidHash3, 2);
        assertEq(registry.getCommitment(testCidHash3).visibility, 2);
    }

    function test_MultipleReportersCanCommit() public {
        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        vm.prank(reporter2);
        registry.commit(testCidHash2, 1);

        assertEq(registry.getCommitment(testCidHash1).submitter, reporter1);
        assertEq(registry.getCommitment(testCidHash2).submitter, reporter2);
    }

    // ============ Deactivation Tests ============

    function test_DeactivateCommitment() public {
        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        assertTrue(registry.isActive(testCidHash1));

        vm.prank(reporter1);
        registry.deactivate(testCidHash1);

        assertFalse(registry.isActive(testCidHash1));
    }

    function test_DeactivateEmitsEvent() public {
        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        vm.expectEmit(true, true, false, false);
        emit ReportDeactivated(testCidHash1, reporter1);

        vm.prank(reporter1);
        registry.deactivate(testCidHash1);
    }

    function test_CommitmentDataPersistsAfterDeactivation() public {
        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        vm.prank(reporter1);
        registry.deactivate(testCidHash1);

        CommitmentRegistry.Commitment memory commitment = registry.getCommitment(testCidHash1);
        assertEq(commitment.cidHash, testCidHash1);
        assertEq(commitment.submitter, reporter1);
        assertFalse(commitment.isActive);
    }

    // ============ Revert Tests ============

    function test_RevertDuplicateCommitment() public {
        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        vm.prank(reporter1);
        vm.expectRevert(CommitmentRegistry.CommitmentAlreadyExists.selector);
        registry.commit(testCidHash1, 1);
    }

    function test_RevertDuplicateFromDifferentAddress() public {
        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        vm.prank(reporter2);
        vm.expectRevert(CommitmentRegistry.CommitmentAlreadyExists.selector);
        registry.commit(testCidHash1, 2);
    }

    function test_RevertUnauthorizedDeactivation() public {
        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        vm.prank(attacker);
        vm.expectRevert(CommitmentRegistry.UnauthorizedDeactivation.selector);
        registry.deactivate(testCidHash1);
    }

    function test_RevertDeactivateNonExistent() public {
        vm.prank(reporter1);
        vm.expectRevert(CommitmentRegistry.CommitmentNotFound.selector);
        registry.deactivate(testCidHash1);
    }

    // ============ Event Tests ============

    function test_CommitEmitsEvent() public {
        vm.expectEmit(true, true, false, true);
        emit ReportCommitted(testCidHash1, reporter1, 1, block.timestamp);

        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);
    }

    // ============ View Function Tests ============

    function test_GetCommitmentReturnsCorrectData() public {
        vm.warp(1000);
        vm.prank(reporter1);
        registry.commit(testCidHash1, 2);

        CommitmentRegistry.Commitment memory commitment = registry.getCommitment(testCidHash1);

        assertEq(commitment.cidHash, testCidHash1);
        assertEq(commitment.submitter, reporter1);
        assertEq(commitment.visibility, 2);
        assertEq(commitment.timestamp, 1000);
        assertTrue(commitment.isActive);
    }

    function test_IsActiveReturnsCorrectValue() public {
        assertFalse(registry.isActive(testCidHash1)); // Non-existent

        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);
        assertTrue(registry.isActive(testCidHash1));

        vm.prank(reporter1);
        registry.deactivate(testCidHash1);
        assertFalse(registry.isActive(testCidHash1));
    }

    // ============ Edge Case Tests ============

    function test_CommitWithZeroCidHash() public {
        // Zero hash should work - it's a valid hash
        vm.prank(reporter1);
        registry.commit(bytes32(0), 1);

        assertTrue(registry.isActive(bytes32(0)));
    }

    function test_CommitWithMaxVisibility() public {
        vm.prank(reporter1);
        registry.commit(testCidHash1, 2);
        assertEq(registry.getCommitment(testCidHash1).visibility, 2);
    }

    function test_CommitAtBlockTimestampZero() public {
        vm.warp(0);
        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        // Timestamp 0 is valid, but getCommitment checks timestamp != 0
        // So this commitment should still be considered valid
        assertEq(registry.getCommitment(testCidHash1).timestamp, 0);
    }

    // ============ Fuzz Tests ============

    function testFuzz_CommitWithAnyValidVisibility(uint8 visibility) public {
        vm.assume(visibility <= 2);

        vm.prank(reporter1);
        registry.commit(testCidHash1, visibility);

        assertEq(registry.getCommitment(testCidHash1).visibility, visibility);
    }

    function testFuzz_CommitWithAnyCidHash(bytes32 cidHash) public {
        vm.prank(reporter1);
        registry.commit(cidHash, 1);

        assertEq(registry.getCommitment(cidHash).cidHash, cidHash);
    }

    function testFuzz_CommitFromAnyAddress(address submitter) public {
        vm.assume(submitter != address(0));

        vm.prank(submitter);
        registry.commit(testCidHash1, 1);

        assertEq(registry.getCommitment(testCidHash1).submitter, submitter);
    }

    // ============ Gas Tests ============

    function test_GasCostSingleCommit() public {
        vm.prank(reporter1);
        uint256 gasBefore = gasleft();
        registry.commit(testCidHash1, 1);
        uint256 gasAfter = gasleft();

        uint256 gasUsed = gasBefore - gasAfter;
        console.log("Gas used for single commit:", gasUsed);

        // Should be under 100k gas
        assertLt(gasUsed, 100000);
    }

    function test_GasCostDeactivate() public {
        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        vm.prank(reporter1);
        uint256 gasBefore = gasleft();
        registry.deactivate(testCidHash1);
        uint256 gasAfter = gasleft();

        uint256 gasUsed = gasBefore - gasAfter;
        console.log("Gas used for deactivate:", gasUsed);

        // Should be under 30k gas
        assertLt(gasUsed, 30000);
    }

    function test_GasCostGetCommitment() public {
        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        uint256 gasBefore = gasleft();
        registry.getCommitment(testCidHash1);
        uint256 gasAfter = gasleft();

        uint256 gasUsed = gasBefore - gasAfter;
        console.log("Gas used for getCommitment:", gasUsed);

        // View function should be very cheap
        assertLt(gasUsed, 10000);
    }

    // ============ Timestamp Tests ============

    function test_CommitmentTimestampIsBlockTimestamp() public {
        uint256 expectedTime = 12345678;
        vm.warp(expectedTime);

        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        assertEq(registry.getCommitment(testCidHash1).timestamp, expectedTime);
    }

    function test_MultipleCommitmentsHaveDifferentTimestamps() public {
        vm.warp(1000);
        vm.prank(reporter1);
        registry.commit(testCidHash1, 1);

        vm.warp(2000);
        vm.prank(reporter1);
        registry.commit(testCidHash2, 1);

        assertEq(registry.getCommitment(testCidHash1).timestamp, 1000);
        assertEq(registry.getCommitment(testCidHash2).timestamp, 2000);
    }
}
