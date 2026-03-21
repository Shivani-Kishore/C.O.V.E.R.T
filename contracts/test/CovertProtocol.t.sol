// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/COVCredits.sol";
import "../src/CovertBadges.sol";
import "../src/CovertProtocol.sol";

/**
 * @title CovertProtocolTest
 * @notice Comprehensive test suite for COVCredits, CovertBadges, and CovertProtocol.
 */
contract CovertProtocolTest is Test {
    COVCredits credits;
    CovertBadges badges;
    CovertProtocol protocol;

    address admin = address(0xA);
    address treasury = address(0xB);
    address reporter1 = address(0x1);
    address supporter1 = address(0x2);
    address challenger1 = address(0x3);
    address reviewer1 = address(0x4);
    address moderator1 = address(0x5);
    address user2 = address(0x6);

    function setUp() public {
        vm.startPrank(admin);

        // Deploy contracts
        credits = new COVCredits(admin);
        badges = new CovertBadges(admin);
        protocol = new CovertProtocol(admin, treasury, address(credits), address(badges));

        // Grant protocol the MINTER and BURNER roles on COVCredits
        credits.grantRole(credits.MINTER_ROLE(), address(protocol));
        credits.grantRole(credits.BURNER_ROLE(), address(protocol));

        // Grant reviewer and moderator roles on protocol
        protocol.grantRole(protocol.REVIEWER_ROLE(), reviewer1);
        protocol.grantRole(protocol.MODERATOR_ROLE(), moderator1);

        vm.stopPrank();
    }

    // ═════════════════════════════════════════════════════
    // COVCredits Tests
    // ═════════════════════════════════════════════════════

    function test_Credits_InitialState() public view {
        assertEq(credits.name(), "COV Credits");
        assertEq(credits.symbol(), "COV");
        assertEq(credits.decimals(), 18);
        assertEq(credits.totalSupply(), 0);
    }

    function test_Credits_WelcomeGrant() public {
        vm.prank(admin);
        credits.grantWelcome(reporter1);

        assertEq(credits.balanceOf(reporter1), 30 ether);
        assertEq(credits.totalSupply(), 30 ether);
        assertTrue(credits.welcomeClaimed(reporter1));
    }

    function test_Credits_WelcomeGrant_CannotClaimTwice() public {
        vm.prank(admin);
        credits.grantWelcome(reporter1);

        vm.prank(admin);
        vm.expectRevert(COVCredits.WelcomeAlreadyClaimed.selector);
        credits.grantWelcome(reporter1);
    }

    function test_Credits_Mint() public {
        vm.prank(admin);
        credits.mint(reporter1, 100 ether);

        assertEq(credits.balanceOf(reporter1), 100 ether);
    }

    function test_Credits_Burn() public {
        vm.prank(admin);
        credits.mint(reporter1, 100 ether);

        vm.prank(admin);
        credits.burn(reporter1, 40 ether);

        assertEq(credits.balanceOf(reporter1), 60 ether);
    }

    function test_Credits_TransferDisabled() public {
        vm.prank(reporter1);
        vm.expectRevert(COVCredits.TransfersDisabled.selector);
        credits.transfer(user2, 1 ether);
    }

    function test_Credits_ApproveDisabled() public {
        vm.prank(reporter1);
        vm.expectRevert(COVCredits.TransfersDisabled.selector);
        credits.approve(user2, 1 ether);
    }

    function test_Credits_TransferFromDisabled() public {
        vm.prank(reporter1);
        vm.expectRevert(COVCredits.TransfersDisabled.selector);
        credits.transferFrom(reporter1, user2, 1 ether);
    }

    function test_Credits_AllowanceReturnsZero() public view {
        assertEq(credits.allowance(reporter1, user2), 0);
    }

    function test_Credits_MaxSupply() public {
        vm.startPrank(admin);
        credits.mint(reporter1, credits.MAX_SUPPLY());

        vm.expectRevert(COVCredits.MaxSupplyExceeded.selector);
        credits.mint(reporter1, 1);
        vm.stopPrank();
    }

    function test_Credits_Pause() public {
        vm.prank(admin);
        credits.pause();

        vm.prank(admin);
        vm.expectRevert();
        credits.mint(reporter1, 1 ether);
    }

    // ═════════════════════════════════════════════════════
    // CovertBadges Tests
    // ═════════════════════════════════════════════════════

    function test_Badges_MintBadge() public {
        vm.prank(admin);
        badges.mintBadge(reporter1, CovertBadges.BadgeType.TIER_0_NEW);

        assertTrue(badges.isBadgeActive(reporter1, CovertBadges.BadgeType.TIER_0_NEW));
        assertEq(badges.ownerOf(1), reporter1);
    }

    function test_Badges_SetInactive() public {
        vm.prank(admin);
        badges.mintBadge(reporter1, CovertBadges.BadgeType.REVIEWER_BADGE);

        vm.prank(admin);
        badges.setBadgeActive(reporter1, CovertBadges.BadgeType.REVIEWER_BADGE, false);

        assertFalse(badges.isBadgeActive(reporter1, CovertBadges.BadgeType.REVIEWER_BADGE));
        // Still owned!
        assertEq(badges.ownerOf(1), reporter1);
    }

    function test_Badges_ReactivateBadge() public {
        vm.prank(admin);
        badges.mintBadge(reporter1, CovertBadges.BadgeType.REVIEWER_BADGE);

        vm.prank(admin);
        badges.setBadgeActive(reporter1, CovertBadges.BadgeType.REVIEWER_BADGE, false);

        vm.prank(admin);
        badges.setBadgeActive(reporter1, CovertBadges.BadgeType.REVIEWER_BADGE, true);

        assertTrue(badges.isBadgeActive(reporter1, CovertBadges.BadgeType.REVIEWER_BADGE));
    }

    function test_Badges_TransferBlocked() public {
        vm.prank(admin);
        badges.mintBadge(reporter1, CovertBadges.BadgeType.TIER_0_NEW);

        vm.prank(reporter1);
        vm.expectRevert(CovertBadges.SoulBoundTransferBlocked.selector);
        badges.transferFrom(reporter1, user2, 1);
    }

    function test_Badges_ApproveBlocked() public {
        vm.prank(admin);
        badges.mintBadge(reporter1, CovertBadges.BadgeType.TIER_0_NEW);

        vm.prank(reporter1);
        vm.expectRevert(CovertBadges.SoulBoundTransferBlocked.selector);
        badges.approve(user2, 1);
    }

    function test_Badges_CannotMintDuplicate() public {
        vm.prank(admin);
        badges.mintBadge(reporter1, CovertBadges.BadgeType.TIER_0_NEW);

        vm.prank(admin);
        vm.expectRevert(CovertBadges.BadgeAlreadyExists.selector);
        badges.mintBadge(reporter1, CovertBadges.BadgeType.TIER_0_NEW);
    }

    function test_Badges_GetUserBadges() public {
        vm.startPrank(admin);
        badges.mintBadge(reporter1, CovertBadges.BadgeType.TIER_0_NEW);
        badges.mintBadge(reporter1, CovertBadges.BadgeType.REVIEWER_BADGE);
        vm.stopPrank();

        (uint256[6] memory tokenIds, bool[6] memory activeStates) = badges.getUserBadges(reporter1);

        assertEq(tokenIds[0], 1); // TIER_0_NEW
        assertTrue(activeStates[0]);
        assertEq(tokenIds[4], 2); // REVIEWER_BADGE
        assertTrue(activeStates[4]);
        assertEq(tokenIds[1], 0); // TIER_1_REGULAR not minted
        assertFalse(activeStates[1]);
    }

    // ═════════════════════════════════════════════════════
    // CovertProtocol Tests
    // ═════════════════════════════════════════════════════

    function _setupUserWithCredits(address user, uint256 amount) internal {
        vm.prank(admin);
        credits.mint(user, amount);
    }

    function _claimWelcome(address user) internal {
        vm.prank(user);
        protocol.claimWelcome();
    }

    function _createPublicReport(address user) internal returns (uint256) {
        vm.prank(user);
        protocol.createReport(CovertProtocol.Visibility.PUBLIC, keccak256("test-report"));
        return protocol.nextReportId() - 1;
    }

    // ── Welcome Claim ──

    function test_Protocol_ClaimWelcome() public {
        _claimWelcome(reporter1);
        assertEq(credits.balanceOf(reporter1), 30 ether);
    }

    function test_Protocol_ClaimWelcome_OnlyOnce() public {
        _claimWelcome(reporter1);
        vm.prank(reporter1);
        vm.expectRevert(COVCredits.WelcomeAlreadyClaimed.selector);
        protocol.claimWelcome();
    }

    // ── Create Report ──

    function test_Protocol_CreateReport_Public() public {
        _setupUserWithCredits(reporter1, 100 ether);

        uint256 id = _createPublicReport(reporter1);

        CovertProtocol.Report memory r = protocol.getReport(id);
        assertEq(r.reporter, reporter1);
        assertEq(uint8(r.visibility), uint8(CovertProtocol.Visibility.PUBLIC));
        assertEq(uint8(r.finalLabel), uint8(CovertProtocol.FinalLabel.UNREVIEWED));
        assertEq(r.lockedReportStake, 10 ether);
        // Credits burned for lock
        assertEq(credits.balanceOf(reporter1), 90 ether);
    }

    function test_Protocol_CreateReport_Private() public {
        _setupUserWithCredits(reporter1, 100 ether);

        vm.prank(reporter1);
        protocol.createReport(CovertProtocol.Visibility.PRIVATE, keccak256("private-report"));

        CovertProtocol.Report memory r = protocol.getReport(0);
        assertEq(r.lockedReportStake, 6 ether);
        assertEq(credits.balanceOf(reporter1), 94 ether);
    }

    function test_Protocol_CreateReport_InsufficientCredits() public {
        _setupUserWithCredits(reporter1, 5 ether);

        vm.prank(reporter1);
        vm.expectRevert(CovertProtocol.InsufficientCredits.selector);
        protocol.createReport(CovertProtocol.Visibility.PUBLIC, keccak256("test"));
    }

    // ── Support ──

    function test_Protocol_Support() public {
        _setupUserWithCredits(reporter1, 100 ether);
        _setupUserWithCredits(supporter1, 100 ether);

        uint256 id = _createPublicReport(reporter1);

        vm.prank(supporter1);
        protocol.support(id, keccak256("I support this"));

        assertTrue(protocol.hasSupported(id, supporter1));
        assertEq(protocol.lockedSupportStake(id, supporter1), 1 ether);
        assertEq(credits.balanceOf(supporter1), 99 ether);
        assertEq(protocol.getSupporterCount(id), 1);
    }

    function test_Protocol_Support_CannotSupportAndChallenge() public {
        _setupUserWithCredits(reporter1, 100 ether);
        _setupUserWithCredits(supporter1, 100 ether);

        uint256 id = _createPublicReport(reporter1);

        vm.prank(supporter1);
        protocol.support(id, keccak256("support"));

        vm.prank(supporter1);
        vm.expectRevert(CovertProtocol.CannotSupportAndChallenge.selector);
        protocol.challenge(id, keccak256("challenge"));
    }

    function test_Protocol_Support_ReporterCannotSupport() public {
        _setupUserWithCredits(reporter1, 100 ether);

        uint256 id = _createPublicReport(reporter1);

        vm.prank(reporter1);
        vm.expectRevert(CovertProtocol.CallerIsReporter.selector);
        protocol.support(id, keccak256("self-support"));
    }

    // ── Challenge ──

    function test_Protocol_Challenge() public {
        _setupUserWithCredits(reporter1, 100 ether);
        _setupUserWithCredits(challenger1, 100 ether);

        uint256 id = _createPublicReport(reporter1);

        vm.prank(challenger1);
        protocol.challenge(id, keccak256("I challenge this"));

        assertTrue(protocol.hasChallenged(id, challenger1));
        assertEq(protocol.lockedChallengeStake(id, challenger1), 3 ether);
        assertEq(credits.balanceOf(challenger1), 97 ether);
        assertEq(protocol.getChallengerCount(id), 1);
    }

    // ── Review Decision ──

    function test_Protocol_SetReviewDecision() public {
        _setupUserWithCredits(reporter1, 100 ether);
        uint256 id = _createPublicReport(reporter1);

        vm.prank(reviewer1);
        protocol.setReviewDecision(id, CovertProtocol.ReviewerDecision.REVIEW_PASSED);

        CovertProtocol.Report memory r = protocol.getReport(id);
        assertEq(uint8(r.reviewDecision), uint8(CovertProtocol.ReviewerDecision.REVIEW_PASSED));
        assertTrue(r.reviewedAt > 0);
    }

    function test_Protocol_SetReviewDecision_NoneReverts() public {
        _setupUserWithCredits(reporter1, 100 ether);
        uint256 id = _createPublicReport(reporter1);

        vm.prank(reviewer1);
        vm.expectRevert(CovertProtocol.InvalidDecision.selector);
        protocol.setReviewDecision(id, CovertProtocol.ReviewerDecision.NONE);
    }

    // ── Appeal ──

    function test_Protocol_Appeal() public {
        _setupUserWithCredits(reporter1, 100 ether);
        uint256 id = _createPublicReport(reporter1);

        vm.prank(reviewer1);
        protocol.setReviewDecision(id, CovertProtocol.ReviewerDecision.REJECT_SPAM);

        vm.prank(reporter1);
        protocol.appeal(id, keccak256("appeal-reason"));

        CovertProtocol.Report memory r = protocol.getReport(id);
        assertTrue(r.hasAppeal);
        assertEq(r.lockedAppealBond, 8 ether);
        assertEq(credits.balanceOf(reporter1), 82 ether); // 100 - 10 (report) - 8 (appeal)
    }

    function test_Protocol_Appeal_OnlyReporter() public {
        _setupUserWithCredits(reporter1, 100 ether);
        uint256 id = _createPublicReport(reporter1);

        vm.prank(reviewer1);
        protocol.setReviewDecision(id, CovertProtocol.ReviewerDecision.REJECT_SPAM);

        vm.prank(supporter1);
        vm.expectRevert(CovertProtocol.OnlyReporter.selector);
        protocol.appeal(id, keccak256("not-reporter"));
    }

    function test_Protocol_Appeal_RequiresReviewDecision() public {
        _setupUserWithCredits(reporter1, 100 ether);
        uint256 id = _createPublicReport(reporter1);

        vm.prank(reporter1);
        vm.expectRevert(CovertProtocol.ReviewDecisionRequired.selector);
        protocol.appeal(id, keccak256("too-early"));
    }

    // ── Finalize: CORROBORATED ──

    function test_Protocol_Finalize_Corroborated() public {
        _setupUserWithCredits(reporter1, 100 ether);
        _setupUserWithCredits(supporter1, 100 ether);
        _setupUserWithCredits(challenger1, 100 ether);

        uint256 id = _createPublicReport(reporter1);

        vm.prank(supporter1);
        protocol.support(id, keccak256("support"));

        vm.prank(challenger1);
        protocol.challenge(id, keccak256("challenge"));

        vm.prank(moderator1);
        protocol.finalizeReport(id, CovertProtocol.FinalLabel.CORROBORATED, CovertProtocol.AppealOutcome.NONE);

        CovertProtocol.Report memory r = protocol.getReport(id);
        assertEq(uint8(r.finalLabel), uint8(CovertProtocol.FinalLabel.CORROBORATED));

        // Reporter: stake returned (10 COV)
        assertEq(credits.balanceOf(reporter1), 100 ether);
        // Supporter: stake returned (1 COV)
        assertEq(credits.balanceOf(supporter1), 100 ether);
        // Challenger: stake returned (not malicious)
        assertEq(credits.balanceOf(challenger1), 100 ether);
    }

    // ── Finalize: FALSE_OR_MANIPULATED ──

    function test_Protocol_Finalize_FalseOrManipulated() public {
        _setupUserWithCredits(reporter1, 100 ether);
        _setupUserWithCredits(supporter1, 100 ether);
        _setupUserWithCredits(challenger1, 100 ether);

        uint256 id = _createPublicReport(reporter1);

        vm.prank(supporter1);
        protocol.support(id, keccak256("support"));

        vm.prank(challenger1);
        protocol.challenge(id, keccak256("challenge"));

        vm.prank(moderator1);
        protocol.finalizeReport(
            id, CovertProtocol.FinalLabel.FALSE_OR_MANIPULATED, CovertProtocol.AppealOutcome.NONE
        );

        // Reporter: stake slashed (10 COV)
        assertEq(credits.balanceOf(reporter1), 90 ether);
        // Supporter: stake slashed (1 COV)
        assertEq(credits.balanceOf(supporter1), 99 ether);
        // Challenger: stake returned (3 COV, not malicious)
        assertEq(credits.balanceOf(challenger1), 100 ether);
        // Treasury gets 11 COV (10 reporter + 1 supporter)
        assertEq(credits.balanceOf(treasury), 11 ether);
    }

    // ── Finalize: Malicious Challenger ──

    function test_Protocol_Finalize_MaliciousChallenger() public {
        _setupUserWithCredits(reporter1, 100 ether);
        _setupUserWithCredits(challenger1, 100 ether);

        uint256 id = _createPublicReport(reporter1);

        vm.prank(challenger1);
        protocol.challenge(id, keccak256("challenge"));

        // Mark challenger as malicious
        vm.prank(moderator1);
        protocol.markMalicious(id, challenger1, true);

        vm.prank(moderator1);
        protocol.finalizeReport(id, CovertProtocol.FinalLabel.CORROBORATED, CovertProtocol.AppealOutcome.NONE);

        // Challenger: stake slashed (3 COV, malicious)
        assertEq(credits.balanceOf(challenger1), 97 ether);
        // Treasury gets 3 COV
        assertEq(credits.balanceOf(treasury), 3 ether);
    }

    // ── Finalize: Appeal Won ──

    function test_Protocol_Finalize_AppealWon() public {
        _setupUserWithCredits(reporter1, 100 ether);
        uint256 id = _createPublicReport(reporter1);

        vm.prank(reviewer1);
        protocol.setReviewDecision(id, CovertProtocol.ReviewerDecision.REJECT_SPAM);

        vm.prank(reporter1);
        protocol.appeal(id, keccak256("appeal"));

        vm.prank(moderator1);
        protocol.finalizeReport(id, CovertProtocol.FinalLabel.CORROBORATED, CovertProtocol.AppealOutcome.APPEAL_WON);

        // Reporter: stake (10) returned + appeal bond (8) returned = 100
        assertEq(credits.balanceOf(reporter1), 100 ether);
    }

    // ── Finalize: Appeal Lost ──

    function test_Protocol_Finalize_AppealLost() public {
        _setupUserWithCredits(reporter1, 100 ether);
        uint256 id = _createPublicReport(reporter1);

        vm.prank(reviewer1);
        protocol.setReviewDecision(id, CovertProtocol.ReviewerDecision.REJECT_SPAM);

        vm.prank(reporter1);
        protocol.appeal(id, keccak256("appeal"));

        vm.prank(moderator1);
        protocol.finalizeReport(
            id, CovertProtocol.FinalLabel.FALSE_OR_MANIPULATED, CovertProtocol.AppealOutcome.APPEAL_LOST
        );

        // Reporter: report stake slashed (10), appeal: 4 returned + 4 slashed
        // 100 - 10 - 8 + 4 = 86
        assertEq(credits.balanceOf(reporter1), 86 ether);
        // Treasury: 10 (report) + 4 (half appeal) = 14
        assertEq(credits.balanceOf(treasury), 14 ether);
    }

    // ── Finalize: Appeal Abusive ──

    function test_Protocol_Finalize_AppealAbusive() public {
        _setupUserWithCredits(reporter1, 100 ether);
        uint256 id = _createPublicReport(reporter1);

        vm.prank(reviewer1);
        protocol.setReviewDecision(id, CovertProtocol.ReviewerDecision.REJECT_SPAM);

        vm.prank(reporter1);
        protocol.appeal(id, keccak256("appeal"));

        vm.prank(moderator1);
        protocol.finalizeReport(
            id, CovertProtocol.FinalLabel.FALSE_OR_MANIPULATED, CovertProtocol.AppealOutcome.APPEAL_ABUSIVE
        );

        // Reporter: report stake slashed (10), appeal bond slashed (8)
        // 100 - 10 - 8 = 82
        assertEq(credits.balanceOf(reporter1), 82 ether);
        // Treasury: 10 + 8 = 18
        assertEq(credits.balanceOf(treasury), 18 ether);
    }

    // ── Finalize: Cannot finalize twice ──

    function test_Protocol_Finalize_CannotFinalizeTwice() public {
        _setupUserWithCredits(reporter1, 100 ether);
        uint256 id = _createPublicReport(reporter1);

        vm.prank(moderator1);
        protocol.finalizeReport(id, CovertProtocol.FinalLabel.CORROBORATED, CovertProtocol.AppealOutcome.NONE);

        vm.prank(moderator1);
        vm.expectRevert(CovertProtocol.AlreadyFinalized.selector);
        protocol.finalizeReport(id, CovertProtocol.FinalLabel.DISPUTED, CovertProtocol.AppealOutcome.NONE);
    }

    // ── Finalize: UNREVIEWED label rejected ──

    function test_Protocol_Finalize_UnreviewedLabelRejected() public {
        _setupUserWithCredits(reporter1, 100 ether);
        uint256 id = _createPublicReport(reporter1);

        vm.prank(moderator1);
        vm.expectRevert(CovertProtocol.InvalidFinalLabel.selector);
        protocol.finalizeReport(id, CovertProtocol.FinalLabel.UNREVIEWED, CovertProtocol.AppealOutcome.NONE);
    }

    // ── Finalize: Appeal outcome mismatch ──

    function test_Protocol_Finalize_AppealOutcomeMismatch_NoAppeal() public {
        _setupUserWithCredits(reporter1, 100 ether);
        uint256 id = _createPublicReport(reporter1);

        vm.prank(moderator1);
        vm.expectRevert(CovertProtocol.AppealOutcomeMismatch.selector);
        protocol.finalizeReport(
            id, CovertProtocol.FinalLabel.CORROBORATED, CovertProtocol.AppealOutcome.APPEAL_WON
        );
    }

    function test_Protocol_Finalize_AppealOutcomeMismatch_HasAppeal() public {
        _setupUserWithCredits(reporter1, 100 ether);
        uint256 id = _createPublicReport(reporter1);

        vm.prank(reviewer1);
        protocol.setReviewDecision(id, CovertProtocol.ReviewerDecision.REJECT_SPAM);

        vm.prank(reporter1);
        protocol.appeal(id, keccak256("appeal"));

        vm.prank(moderator1);
        vm.expectRevert(CovertProtocol.AppealOutcomeMismatch.selector);
        protocol.finalizeReport(id, CovertProtocol.FinalLabel.CORROBORATED, CovertProtocol.AppealOutcome.NONE);
    }

    // ── Automation Role: Reviewer management ──

    function test_Automation_CanGrantReviewerRole() public {
        address automationWallet = address(0x7);
        address newReviewer = address(0x8);
        // Pre-cache to avoid vm.prank being consumed by the constant getter staticcall.
        bytes32 automationRole = protocol.AUTOMATION_ROLE();
        bytes32 reviewerRole = protocol.REVIEWER_ROLE();

        // Grant AUTOMATION_ROLE to the automation wallet (admin has DEFAULT_ADMIN_ROLE)
        vm.prank(admin);
        protocol.grantRole(automationRole, automationWallet);

        // Automation wallet can now grant REVIEWER_ROLE (role admin = AUTOMATION_ROLE per §8.3)
        vm.prank(automationWallet);
        protocol.grantRole(reviewerRole, newReviewer);

        assertTrue(protocol.hasRole(reviewerRole, newReviewer));
    }

    function test_Automation_CanRevokeReviewerRole() public {
        address automationWallet = address(0x7);
        bytes32 automationRole = protocol.AUTOMATION_ROLE();
        bytes32 reviewerRole = protocol.REVIEWER_ROLE();

        vm.prank(admin);
        protocol.grantRole(automationRole, automationWallet);

        // Automation wallet revokes an existing reviewer
        vm.prank(automationWallet);
        protocol.revokeRole(reviewerRole, reviewer1);

        assertFalse(protocol.hasRole(reviewerRole, reviewer1));
    }

    function test_Automation_NonAutomationCannotGrantReviewerRole() public {
        address rando = address(0x9);
        bytes32 reviewerRole = protocol.REVIEWER_ROLE();

        vm.prank(rando);
        vm.expectRevert();
        protocol.grantRole(reviewerRole, rando);
    }

    // ── Role Exclusivity ──

    function test_RoleExclusivity_CannotGrantReviewerToModerator() public {
        // reviewer1 already has REVIEWER_ROLE; try to grant them MODERATOR_ROLE too
        bytes32 modRole = protocol.MODERATOR_ROLE();
        vm.prank(admin);
        vm.expectRevert(CovertProtocol.RoleConflict.selector);
        protocol.grantRole(modRole, reviewer1);
    }

    function test_RoleExclusivity_CannotGrantModeratorToReviewer() public {
        // moderator1 already has MODERATOR_ROLE; try to grant REVIEWER_ROLE
        bytes32 automationRole = protocol.AUTOMATION_ROLE();
        bytes32 reviewerRole   = protocol.REVIEWER_ROLE();
        address newReviewer    = address(0xAA);

        // Give newReviewer REVIEWER_ROLE first
        vm.prank(admin);
        protocol.grantRole(automationRole, admin); // admin already has it, no-op
        vm.prank(admin);
        protocol.grantRole(reviewerRole, newReviewer);

        // Now try granting MODERATOR_ROLE to the same address
        bytes32 modRole = protocol.MODERATOR_ROLE();
        vm.prank(admin);
        vm.expectRevert(CovertProtocol.RoleConflict.selector);
        protocol.grantRole(modRole, newReviewer);
    }

    // ── Self-Review Prevention ──

    function test_SelfReview_ReviewerCannotReviewOwnReport() public {
        // reviewer1 submits a report
        _claimWelcome(reviewer1);
        vm.prank(reviewer1);
        protocol.createReport(CovertProtocol.Visibility.PUBLIC, keccak256("reviewer-own-report"));
        uint256 id = protocol.nextReportId() - 1;

        // reviewer1 tries to set a review decision on their own report
        vm.prank(reviewer1);
        vm.expectRevert(CovertProtocol.CallerIsReporter.selector);
        protocol.setReviewDecision(id, CovertProtocol.ReviewerDecision.REVIEW_PASSED);
    }

    function test_SelfReview_ModeratorCannotFinalizeOwnReport() public {
        // moderator1 submits a report
        _claimWelcome(moderator1);
        vm.prank(moderator1);
        protocol.createReport(CovertProtocol.Visibility.PUBLIC, keccak256("moderator-own-report"));
        uint256 id = protocol.nextReportId() - 1;

        // reviewer sets a decision first (required by finalizeReport flow — not strictly enforced
        // in the contract but let's use a valid path; here we skip that and test the reporter check)
        vm.prank(moderator1);
        vm.expectRevert(CovertProtocol.CallerIsReporter.selector);
        protocol.finalizeReport(id, CovertProtocol.FinalLabel.CORROBORATED, CovertProtocol.AppealOutcome.NONE);
    }

    function test_SelfReview_ModeratorCannotMarkMaliciousOnOwnReport() public {
        // moderator1 submits a report
        _claimWelcome(moderator1);
        vm.prank(moderator1);
        protocol.createReport(CovertProtocol.Visibility.PUBLIC, keccak256("moderator-mark-own"));
        uint256 id = protocol.nextReportId() - 1;

        vm.prank(moderator1);
        vm.expectRevert(CovertProtocol.CallerIsReporter.selector);
        protocol.markMalicious(id, address(0x999), true);
    }

    // ── End-to-End: Full lifecycle ──

    function test_Protocol_FullLifecycle() public {
        // Setup
        _claimWelcome(reporter1);
        _claimWelcome(supporter1);
        _claimWelcome(challenger1);

        // Create report (costs 10 COV)
        vm.prank(reporter1);
        protocol.createReport(CovertProtocol.Visibility.PUBLIC, keccak256("full-lifecycle"));
        uint256 id = 0;

        // Support (costs 1 COV)
        vm.prank(supporter1);
        protocol.support(id, keccak256("I support"));

        // Challenge (costs 3 COV)
        vm.prank(challenger1);
        protocol.challenge(id, keccak256("I challenge"));

        // Review
        vm.prank(reviewer1);
        protocol.setReviewDecision(id, CovertProtocol.ReviewerDecision.REVIEW_PASSED);

        // Finalize as CORROBORATED
        vm.prank(moderator1);
        protocol.finalizeReport(id, CovertProtocol.FinalLabel.CORROBORATED, CovertProtocol.AppealOutcome.NONE);

        // Verify final state
        assertEq(credits.balanceOf(reporter1), 30 ether); // all returned
        assertEq(credits.balanceOf(supporter1), 30 ether); // all returned
        assertEq(credits.balanceOf(challenger1), 30 ether); // returned (not malicious)
        assertEq(credits.balanceOf(treasury), 0); // nothing slashed
    }
}
