// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./COVCredits.sol";
import "./CovertBadges.sol";

/**
 * @title CovertProtocol
 * @notice Core protocol for C.O.V.E.R.T: reports, staking, review,
 *         moderation finalization, and settlement.
 * @dev    Stake locking is implemented via burn-on-lock / mint-on-return.
 */
contract CovertProtocol is AccessControl, ReentrancyGuard {
    // ───────────── External Contracts ─────────────
    COVCredits public immutable covCredits;
    CovertBadges public immutable covBadges;

    // ───────────── Constants (fixed stakes) ─────────────
    uint256 public constant REPORT_STAKE_PUBLIC = 10 * 10 ** 18;
    uint256 public constant REPORT_STAKE_PRIVATE = 6 * 10 ** 18;
    uint256 public constant SUPPORT_STAKE = 1 * 10 ** 18;
    uint256 public constant CHALLENGE_STAKE = 3 * 10 ** 18;
    uint256 public constant APPEAL_BOND = 8 * 10 ** 18;

    // ───────────── Roles ─────────────
    bytes32 public constant REVIEWER_ROLE = keccak256("REVIEWER_ROLE");
    bytes32 public constant MODERATOR_ROLE = keccak256("MODERATOR_ROLE");
    bytes32 public constant AUTOMATION_ROLE = keccak256("AUTOMATION_ROLE");

    // ───────────── Enums ─────────────
    enum Visibility { PUBLIC, PRIVATE }

    enum ReviewerDecision { NONE, NEEDS_EVIDENCE, REVIEW_PASSED, REJECT_SPAM }

    enum FinalLabel { UNREVIEWED, NEEDS_EVIDENCE, CORROBORATED, DISPUTED, FALSE_OR_MANIPULATED }

    enum AppealOutcome { NONE, APPEAL_WON, APPEAL_LOST, APPEAL_ABUSIVE }

    // ───────────── Stake-type identifiers ─────────────
    bytes32 public constant STAKE_REPORT = keccak256("REPORT");
    bytes32 public constant STAKE_SUPPORT = keccak256("SUPPORT");
    bytes32 public constant STAKE_CHALLENGE = keccak256("CHALLENGE");
    bytes32 public constant STAKE_APPEAL = keccak256("APPEAL");

    // ───────────── Report Struct ─────────────
    struct Report {
        address reporter;
        Visibility visibility;
        bytes32 contentHash;
        FinalLabel finalLabel;
        ReviewerDecision reviewDecision;
        uint64 createdAt;
        uint64 reviewedAt;
        uint64 finalizedAt;
        bool hasAppeal;
        bytes32 appealReasonHash;
        uint256 lockedReportStake;
        uint256 lockedAppealBond;
    }

    // ───────────── State ─────────────
    uint256 public nextReportId;
    mapping(uint256 => Report) public reports;

    /// @dev Per-report per-user action tracking.
    mapping(uint256 => mapping(address => bool)) public hasSupported;
    mapping(uint256 => mapping(address => bool)) public hasChallenged;
    mapping(uint256 => mapping(address => uint256)) public lockedSupportStake;
    mapping(uint256 => mapping(address => uint256)) public lockedChallengeStake;
    mapping(uint256 => mapping(address => bool)) public malicious;

    /// @dev Track supporters/challengers lists for settlement iteration.
    mapping(uint256 => address[]) internal _supporters;
    mapping(uint256 => address[]) internal _challengers;

    /// @dev Global locked balance ledger (per user, total across all reports).
    mapping(address => uint256) public lockedBalance;

    /// @notice Treasury address that receives slashed credits.
    address public treasury;

    // ───────────── Events ─────────────
    event WelcomeClaimed(address indexed user, uint256 amount);
    event ReportCreated(
        uint256 indexed reportId,
        address indexed reporter,
        Visibility visibility,
        uint256 stake,
        bytes32 contentHash
    );
    event Supported(uint256 indexed reportId, address indexed user, bytes32 reasonHash);
    event Challenged(uint256 indexed reportId, address indexed user, bytes32 reasonHash);
    event ReviewDecisionSet(uint256 indexed reportId, address indexed reviewer, ReviewerDecision decision);
    event Appealed(uint256 indexed reportId, address indexed reporter, bytes32 appealReasonHash);
    event MarkedMalicious(uint256 indexed reportId, address indexed actor, bool isMalicious);
    event Finalized(
        uint256 indexed reportId,
        address indexed moderator,
        FinalLabel finalLabel,
        AppealOutcome appealOutcome
    );
    event StakeReturned(uint256 indexed reportId, address indexed user, uint256 amount, bytes32 stakeType);
    event StakeSlashed(uint256 indexed reportId, address indexed user, uint256 amount, bytes32 stakeType);

    // ───────────── Errors ─────────────
    error ReportNotFound();
    error AlreadyFinalized();
    error InsufficientCredits();
    error AlreadySupported();
    error AlreadyChallenged();
    error CannotSupportAndChallenge();
    error OnlyReporter();
    error ReviewDecisionRequired();
    error AlreadyAppealed();
    error InvalidFinalLabel();
    error AppealOutcomeMismatch();
    error InvalidDecision();
    error CallerIsReporter();
    error RoleConflict();

    // ───────────── Constructor ─────────────
    constructor(address admin, address _treasury, address _covCredits, address _covBadges) {
        covCredits = COVCredits(_covCredits);
        covBadges = CovertBadges(_covBadges);
        treasury = _treasury;

        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MODERATOR_ROLE, admin);
        _grantRole(AUTOMATION_ROLE, admin);

        // Allow automation worker to grant/revoke REVIEWER_ROLE without full admin rights.
        // Spec §8.3: automated worker triggers REVIEWER_ROLE changes based on rep thresholds.
        _setRoleAdmin(REVIEWER_ROLE, AUTOMATION_ROLE);
    }

    // ───────────── Role Management ─────────────

    /**
     * @notice Enforces mutual exclusivity between REVIEWER_ROLE and MODERATOR_ROLE.
     *         A single account may hold one or the other, never both.
     */
    function grantRole(bytes32 role, address account) public override {
        if (role == REVIEWER_ROLE && hasRole(MODERATOR_ROLE, account)) revert RoleConflict();
        if (role == MODERATOR_ROLE && hasRole(REVIEWER_ROLE, account)) revert RoleConflict();
        super.grantRole(role, account);
    }

    // ───────────── Admin ─────────────
    function setTreasury(address _treasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_treasury != address(0), "Treasury cannot be zero address");
        treasury = _treasury;
    }

    // ───────────── Modifiers ─────────────
    modifier reportExists(uint256 reportId) {
        if (reports[reportId].createdAt == 0) revert ReportNotFound();
        _;
    }

    modifier notFinalized(uint256 reportId) {
        if (reports[reportId].finalizedAt != 0) revert AlreadyFinalized();
        _;
    }

    // ───────────── 7 · Welcome Claim ─────────────

    /**
     * @notice Claim the one-time 30 COV welcome grant.
     */
    function claimWelcome() external {
        covCredits.grantWelcome(msg.sender);
        emit WelcomeClaimed(msg.sender, covCredits.WELCOME_GRANT());
    }

    // ───────────── 5.1 · Create Report ─────────────

    /**
     * @notice Submit a new report with a content hash.
     * @param visibility PUBLIC or PRIVATE.
     * @param contentHash keccak256 of the IPFS CID or content reference.
     */
    function createReport(Visibility visibility, bytes32 contentHash) external nonReentrant {
        uint256 stake = visibility == Visibility.PUBLIC ? REPORT_STAKE_PUBLIC : REPORT_STAKE_PRIVATE;

        _lockCredits(msg.sender, stake);

        uint256 reportId = nextReportId++;
        reports[reportId] = Report({
            reporter: msg.sender,
            visibility: visibility,
            contentHash: contentHash,
            finalLabel: FinalLabel.UNREVIEWED,
            reviewDecision: ReviewerDecision.NONE,
            createdAt: uint64(block.timestamp),
            reviewedAt: 0,
            finalizedAt: 0,
            hasAppeal: false,
            appealReasonHash: bytes32(0),
            lockedReportStake: stake,
            lockedAppealBond: 0
        });

        emit ReportCreated(reportId, msg.sender, visibility, stake, contentHash);
    }

    // ───────────── 5.2 · Support ─────────────

    /**
     * @notice Support a report by staking 1 COV.
     * @param reportId Report to support.
     * @param reasonHash Hash of the reason text.
     */
    function support(uint256 reportId, bytes32 reasonHash)
        external
        nonReentrant
        reportExists(reportId)
        notFinalized(reportId)
    {
        if (msg.sender == reports[reportId].reporter) revert CallerIsReporter();
        if (hasSupported[reportId][msg.sender]) revert AlreadySupported();
        if (hasChallenged[reportId][msg.sender]) revert CannotSupportAndChallenge();

        _lockCredits(msg.sender, SUPPORT_STAKE);

        hasSupported[reportId][msg.sender] = true;
        lockedSupportStake[reportId][msg.sender] = SUPPORT_STAKE;
        _supporters[reportId].push(msg.sender);

        emit Supported(reportId, msg.sender, reasonHash);
    }

    // ───────────── 5.3 · Challenge ─────────────

    /**
     * @notice Challenge a report by staking 3 COV.
     * @param reportId Report to challenge.
     * @param reasonHash Hash of the reason text.
     */
    function challenge(uint256 reportId, bytes32 reasonHash)
        external
        nonReentrant
        reportExists(reportId)
        notFinalized(reportId)
    {
        if (msg.sender == reports[reportId].reporter) revert CallerIsReporter();
        if (hasChallenged[reportId][msg.sender]) revert AlreadyChallenged();
        if (hasSupported[reportId][msg.sender]) revert CannotSupportAndChallenge();

        _lockCredits(msg.sender, CHALLENGE_STAKE);

        hasChallenged[reportId][msg.sender] = true;
        lockedChallengeStake[reportId][msg.sender] = CHALLENGE_STAKE;
        _challengers[reportId].push(msg.sender);

        emit Challenged(reportId, msg.sender, reasonHash);
    }

    // ───────────── 5.4 · Set Review Decision ─────────────

    /**
     * @notice Reviewer sets a decision on a report.
     * @param reportId  Report to review.
     * @param decision  One of NEEDS_EVIDENCE, REVIEW_PASSED, REJECT_SPAM.
     */
    function setReviewDecision(uint256 reportId, ReviewerDecision decision)
        external
        onlyRole(REVIEWER_ROLE)
        reportExists(reportId)
        notFinalized(reportId)
    {
        if (msg.sender == reports[reportId].reporter) revert CallerIsReporter();
        if (decision == ReviewerDecision.NONE) revert InvalidDecision();

        reports[reportId].reviewDecision = decision;
        reports[reportId].reviewedAt = uint64(block.timestamp);

        emit ReviewDecisionSet(reportId, msg.sender, decision);
    }

    // ───────────── 5.5 · Appeal (Reporter only) ─────────────

    /**
     * @notice Reporter appeals a reviewer decision by posting an 8 COV bond.
     * @param reportId           Report to appeal.
     * @param appealReasonHash   Hash of the appeal reason text.
     */
    function appeal(uint256 reportId, bytes32 appealReasonHash)
        external
        nonReentrant
        reportExists(reportId)
        notFinalized(reportId)
    {
        Report storage r = reports[reportId];
        if (msg.sender != r.reporter) revert OnlyReporter();
        if (r.reviewDecision == ReviewerDecision.NONE) revert ReviewDecisionRequired();
        if (r.hasAppeal) revert AlreadyAppealed();

        _lockCredits(msg.sender, APPEAL_BOND);

        r.hasAppeal = true;
        r.appealReasonHash = appealReasonHash;
        r.lockedAppealBond = APPEAL_BOND;

        emit Appealed(reportId, msg.sender, appealReasonHash);
    }

    // ───────────── 5.6 · Mark Malicious ─────────────

    /**
     * @notice Moderator marks an actor on a report as malicious.
     * @param reportId    Report ID.
     * @param actor       User to flag.
     * @param isMalicious True to flag, false to unflag.
     */
    function markMalicious(uint256 reportId, address actor, bool isMalicious)
        external
        onlyRole(MODERATOR_ROLE)
        reportExists(reportId)
        notFinalized(reportId)
    {
        if (msg.sender == reports[reportId].reporter) revert CallerIsReporter();
        malicious[reportId][actor] = isMalicious;
        emit MarkedMalicious(reportId, actor, isMalicious);
    }

    // ───────────── 5.7 · Finalize Report ─────────────

    /**
     * @notice Moderator finalizes a report and settles all stakes.
     * @param reportId      Report to finalize.
     * @param label         One of NEEDS_EVIDENCE, CORROBORATED, DISPUTED, FALSE_OR_MANIPULATED.
     * @param appealOutcome NONE if no appeal; otherwise APPEAL_WON, APPEAL_LOST, APPEAL_ABUSIVE.
     */
    function finalizeReport(uint256 reportId, FinalLabel label, AppealOutcome appealOutcome)
        external
        onlyRole(MODERATOR_ROLE)
        reportExists(reportId)
        notFinalized(reportId)
        nonReentrant
    {
        Report storage r = reports[reportId];

        if (msg.sender == r.reporter) revert CallerIsReporter();
        if (label == FinalLabel.UNREVIEWED) revert InvalidFinalLabel();
        if (!r.hasAppeal && appealOutcome != AppealOutcome.NONE) revert AppealOutcomeMismatch();
        if (r.hasAppeal && appealOutcome == AppealOutcome.NONE) revert AppealOutcomeMismatch();

        r.finalLabel = label;
        r.finalizedAt = uint64(block.timestamp);

        // ── A) Settle reporter's report stake ──
        _settleReportStake(reportId, r, label);

        // ── B) Settle supporter stakes ──
        _settleSupporterStakes(reportId, label);

        // ── C) Settle challenger stakes ──
        _settleChallengerStakes(reportId);

        // ── D) Settle appeal bond ──
        if (r.hasAppeal) {
            _settleAppealBond(reportId, r, appealOutcome);
        }

        emit Finalized(reportId, msg.sender, label, appealOutcome);
    }

    // ───────────── View helpers ─────────────

    function getReport(uint256 reportId) external view returns (Report memory) {
        return reports[reportId];
    }

    function getSupporters(uint256 reportId) external view returns (address[] memory) {
        return _supporters[reportId];
    }

    function getChallengers(uint256 reportId) external view returns (address[] memory) {
        return _challengers[reportId];
    }

    function getSupporterCount(uint256 reportId) external view returns (uint256) {
        return _supporters[reportId].length;
    }

    function getChallengerCount(uint256 reportId) external view returns (uint256) {
        return _challengers[reportId].length;
    }

    // ───────────── Internal: Lock / Return / Slash ─────────────

    /**
     * @dev Lock credits by burning them from the user and tracking in lockedBalance.
     */
    function _lockCredits(address user, uint256 amount) internal {
        if (covCredits.balanceOf(user) < amount) revert InsufficientCredits();
        covCredits.burn(user, amount);
        lockedBalance[user] += amount;
    }

    /**
     * @dev Return previously-locked credits by minting them back to the user.
     */
    function _returnCredits(address user, uint256 amount) internal {
        require(
            lockedBalance[user] >= amount,
            "CovertProtocol: insufficient locked balance to return"
        );
        lockedBalance[user] -= amount;
        covCredits.mint(user, amount);
    }

    /**
     * @dev Slash previously-locked credits by minting them to the treasury.
     */
    function _slashCredits(address user, uint256 amount) internal {
        require(
            lockedBalance[user] >= amount,
            "CovertProtocol: insufficient locked balance to slash"
        );
        lockedBalance[user] -= amount;
        covCredits.mint(treasury, amount);
    }

    // ───────────── Internal: Settlement Logic ─────────────

    function _settleReportStake(uint256 reportId, Report storage r, FinalLabel label) internal {
        uint256 s = r.lockedReportStake;
        if (s == 0) return;

        r.lockedReportStake = 0;

        if (label == FinalLabel.FALSE_OR_MANIPULATED) {
            _slashCredits(r.reporter, s);
            emit StakeSlashed(reportId, r.reporter, s, STAKE_REPORT);
        } else {
            _returnCredits(r.reporter, s);
            emit StakeReturned(reportId, r.reporter, s, STAKE_REPORT);
        }
    }

    function _settleSupporterStakes(uint256 reportId, FinalLabel label) internal {
        address[] storage supporters = _supporters[reportId];
        for (uint256 i = 0; i < supporters.length; i++) {
            address u = supporters[i];
            uint256 s = lockedSupportStake[reportId][u];
            if (s == 0) continue;

            lockedSupportStake[reportId][u] = 0;

            if (label == FinalLabel.FALSE_OR_MANIPULATED) {
                _slashCredits(u, s);
                emit StakeSlashed(reportId, u, s, STAKE_SUPPORT);
            } else {
                _returnCredits(u, s);
                emit StakeReturned(reportId, u, s, STAKE_SUPPORT);
            }
        }
    }

    function _settleChallengerStakes(uint256 reportId) internal {
        address[] storage challengers = _challengers[reportId];
        for (uint256 i = 0; i < challengers.length; i++) {
            address u = challengers[i];
            uint256 s = lockedChallengeStake[reportId][u];
            if (s == 0) continue;

            lockedChallengeStake[reportId][u] = 0;

            if (malicious[reportId][u]) {
                _slashCredits(u, s);
                emit StakeSlashed(reportId, u, s, STAKE_CHALLENGE);
            } else {
                _returnCredits(u, s);
                emit StakeReturned(reportId, u, s, STAKE_CHALLENGE);
            }
        }
    }

    function _settleAppealBond(uint256 reportId, Report storage r, AppealOutcome outcome) internal {
        uint256 bond = r.lockedAppealBond;
        if (bond == 0) return;

        r.lockedAppealBond = 0;

        if (outcome == AppealOutcome.APPEAL_WON) {
            _returnCredits(r.reporter, bond);
            emit StakeReturned(reportId, r.reporter, bond, STAKE_APPEAL);
        } else if (outcome == AppealOutcome.APPEAL_LOST) {
            uint256 half = bond / 2; // 4 COV
            _returnCredits(r.reporter, half);
            emit StakeReturned(reportId, r.reporter, half, STAKE_APPEAL);
            _slashCredits(r.reporter, bond - half);
            emit StakeSlashed(reportId, r.reporter, bond - half, STAKE_APPEAL);
        } else if (outcome == AppealOutcome.APPEAL_ABUSIVE) {
            _slashCredits(r.reporter, bond);
            emit StakeSlashed(reportId, r.reporter, bond, STAKE_APPEAL);
        }
    }
}
