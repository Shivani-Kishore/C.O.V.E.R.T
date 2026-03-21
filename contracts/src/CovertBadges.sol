// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

/**
 * @title CovertBadges
 * @notice Non-transferable Soul-Bound Token (SBT) badges for C.O.V.E.R.T.
 * @dev    Badges can be minted and activated/deactivated but NEVER transferred.
 *         Each user can hold at most one badge per badge type.
 */
contract CovertBadges is ERC721, AccessControl {
    // ───────────── Badge Types ─────────────
    enum BadgeType {
        TIER_0_NEW,         // 0
        TIER_1_REGULAR,     // 1
        TIER_2_TRUSTED,     // 2
        TIER_3_POWER,       // 3
        REVIEWER_BADGE,     // 4
        MODERATOR_BADGE     // 5
    }

    // ───────────── Roles ─────────────
    bytes32 public constant BADGE_MANAGER_ROLE = keccak256("BADGE_MANAGER_ROLE");

    // ───────────── State ─────────────
    /// @notice Whether a tokenId is currently active.
    mapping(uint256 => bool) public active;

    /// @notice Mapping: user => badgeType => tokenId (0 means not minted).
    mapping(address => mapping(BadgeType => uint256)) public badgeTokenId;

    /// @notice Mapping: tokenId => BadgeType (reverse lookup).
    mapping(uint256 => BadgeType) public tokenBadgeType;

    /// @notice Auto-incrementing token ID counter. Starts at 1 so 0 means "none".
    uint256 private _nextTokenId;

    // ───────────── Events ─────────────
    event BadgeMinted(address indexed user, BadgeType badgeType, uint256 tokenId);
    event BadgeActivationChanged(address indexed user, BadgeType badgeType, uint256 tokenId, bool isActive);

    // ───────────── Errors ─────────────
    error BadgeAlreadyExists();
    error BadgeNotFound();
    error SoulBoundTransferBlocked();

    // ───────────── Constructor ─────────────
    constructor(address admin) ERC721("COVERT Badge", "CBADGE") {
        _nextTokenId = 1; // reserve 0 as sentinel
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(BADGE_MANAGER_ROLE, admin);
    }

    // ───────────── Override supportsInterface ─────────────
    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }

    // ───────────── Soul-Bound: Block all transfers ─────────────
    /**
     * @dev Override the internal _update hook that ERC721 calls for
     *      mint / burn / transfer. We allow minting (from == address(0))
     *      but revert on any actual transfer.
     */
    function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
        address from = _ownerOf(tokenId);

        // Allow minting (from is zero) but block all transfers
        if (from != address(0) && to != address(0)) {
            revert SoulBoundTransferBlocked();
        }

        return super._update(to, tokenId, auth);
    }

    /// @dev Block approvals (soul-bound token).
    function approve(address, uint256) public pure override {
        revert SoulBoundTransferBlocked();
    }

    /// @dev Block approvals (soul-bound token).
    function setApprovalForAll(address, bool) public pure override {
        revert SoulBoundTransferBlocked();
    }

    // ───────────── Badge Management ─────────────

    /**
     * @notice Mint a new badge to a user.
     * @param user      Recipient of the badge.
     * @param badgeType Type of badge to mint.
     */
    function mintBadge(address user, BadgeType badgeType) external onlyRole(BADGE_MANAGER_ROLE) {
        if (badgeTokenId[user][badgeType] != 0) revert BadgeAlreadyExists();

        uint256 tokenId = _nextTokenId++;
        _safeMint(user, tokenId);

        badgeTokenId[user][badgeType] = tokenId;
        tokenBadgeType[tokenId] = badgeType;
        active[tokenId] = true;

        emit BadgeMinted(user, badgeType, tokenId);
    }

    /**
     * @notice Activate or deactivate a badge (do NOT burn).
     * @param user      Owner of the badge.
     * @param badgeType Which badge type.
     * @param isActive  true = active, false = inactive.
     */
    function setBadgeActive(address user, BadgeType badgeType, bool isActive) external onlyRole(BADGE_MANAGER_ROLE) {
        uint256 tokenId = badgeTokenId[user][badgeType];
        if (tokenId == 0) revert BadgeNotFound();

        active[tokenId] = isActive;

        emit BadgeActivationChanged(user, badgeType, tokenId, isActive);
    }

    /**
     * @notice Check whether a user's badge of a given type is active.
     * @param user      Address to query.
     * @param badgeType Badge type to check.
     * @return True if the badge exists AND is active.
     */
    function isBadgeActive(address user, BadgeType badgeType) external view returns (bool) {
        uint256 tokenId = badgeTokenId[user][badgeType];
        if (tokenId == 0) return false;
        return active[tokenId];
    }

    /**
     * @notice Get all badge states for a user.
     * @param user Address to query.
     * @return tokenIds Array of 6 token IDs (one per BadgeType, 0 if not minted).
     * @return activeStates Array of 6 booleans (active status per BadgeType).
     */
    function getUserBadges(address user) external view returns (uint256[6] memory tokenIds, bool[6] memory activeStates) {
        for (uint256 i = 0; i < 6; i++) {
            uint256 tid = badgeTokenId[user][BadgeType(i)];
            tokenIds[i] = tid;
            activeStates[i] = tid != 0 && active[tid];
        }
    }
}
