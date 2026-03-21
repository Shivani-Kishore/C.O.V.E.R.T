// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title COVCredits
 * @notice Non-transferable fungible credits for C.O.V.E.R.T protocol.
 * @dev ERC20-like interface but all transfer/approve functions revert.
 *      Only addresses with MINTER_ROLE can mint; only BURNER_ROLE can burn.
 */
contract COVCredits is AccessControl, Pausable {
    // ───────────── Constants ─────────────
    string public constant name = "COV Credits";
    string public constant symbol = "COV";
    uint8 public constant decimals = 18;

    uint256 public constant WELCOME_GRANT = 30 * 10 ** 18;
    uint256 public constant MAX_SUPPLY = 100_000_000 * 10 ** 18;

    // ───────────── Roles ─────────────
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant BURNER_ROLE = keccak256("BURNER_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    // ───────────── State ─────────────
    mapping(address => uint256) public balances;
    mapping(address => bool) public welcomeClaimed;
    uint256 public totalSupply;

    // ───────────── Events ─────────────
    event WelcomeGranted(address indexed user, uint256 amount);
    event Minted(address indexed to, uint256 amount);
    event Burned(address indexed from, uint256 amount);

    // ───────────── Errors ─────────────
    error TransfersDisabled();
    error WelcomeAlreadyClaimed();
    error MaxSupplyExceeded();
    error InsufficientBalance();

    // ───────────── Constructor ─────────────
    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MINTER_ROLE, admin);
        _grantRole(BURNER_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
    }

    // ───────────── ERC20-like View Functions ─────────────
    function balanceOf(address account) external view returns (uint256) {
        return balances[account];
    }

    /// @notice Allowance always returns 0 (transfers disabled).
    function allowance(address, address) external pure returns (uint256) {
        return 0;
    }

    // ───────────── Disabled Transfer Functions ─────────────
    function transfer(address, uint256) external pure returns (bool) {
        revert TransfersDisabled();
    }

    function approve(address, uint256) external pure returns (bool) {
        revert TransfersDisabled();
    }

    function transferFrom(address, address, uint256) external pure returns (bool) {
        revert TransfersDisabled();
    }

    // ───────────── Minting ─────────────

    /**
     * @notice Grant the one-time welcome bonus (30 COV) to a user.
     * @param user Recipient wallet address.
     */
    function grantWelcome(address user) external onlyRole(MINTER_ROLE) whenNotPaused {
        if (welcomeClaimed[user]) revert WelcomeAlreadyClaimed();
        if (totalSupply + WELCOME_GRANT > MAX_SUPPLY) revert MaxSupplyExceeded();

        welcomeClaimed[user] = true;
        _mint(user, WELCOME_GRANT);

        emit WelcomeGranted(user, WELCOME_GRANT);
    }

    /**
     * @notice Mint credits to an address (protocol rewards, etc.).
     * @param to   Recipient address.
     * @param amount Amount of credits (18 decimals).
     */
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) whenNotPaused {
        if (totalSupply + amount > MAX_SUPPLY) revert MaxSupplyExceeded();
        _mint(to, amount);
    }

    /**
     * @notice Burn (slash) credits from an address.
     * @param from   Address to burn from.
     * @param amount Amount to burn.
     */
    function burn(address from, uint256 amount) external onlyRole(BURNER_ROLE) {
        if (balances[from] < amount) revert InsufficientBalance();
        balances[from] -= amount;
        totalSupply -= amount;

        emit Burned(from, amount);
    }

    // ───────────── Pause ─────────────
    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    // ───────────── Internal ─────────────
    function _mint(address to, uint256 amount) internal {
        balances[to] += amount;
        totalSupply += amount;

        emit Minted(to, amount);
    }
}
