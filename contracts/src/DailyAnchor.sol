// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title DailyAnchor
 * @notice Anchors daily moderation logs to the blockchain for integrity verification
 * @dev Posts one Merkle root per day to prove moderation log wasn't tampered with
 */
contract DailyAnchor {
    /// @notice Represents a daily anchor
    struct Anchor {
        bytes32 merkleRoot;     // Merkle root of all moderation actions for the day
        uint256 actionCount;    // Number of actions included
        uint256 timestamp;      // Block timestamp
        address operator;       // Who submitted the anchor
    }

    /// @notice Mapping from date (YYYYMMDD) to anchor
    mapping(uint256 => Anchor) public anchors;

    /// @notice Authorized operators who can submit anchors
    mapping(address => bool) public operators;

    /// @notice Contract owner
    address public owner;

    /// @notice Events
    event AnchorSubmitted(
        uint256 indexed date,
        bytes32 merkleRoot,
        uint256 actionCount,
        address operator
    );

    event OperatorAdded(address indexed operator);
    event OperatorRemoved(address indexed operator);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    /// @notice Errors
    error UnauthorizedOperator();
    error AnchorAlreadyExists();
    error OnlyOwner();
    error ZeroAddress();

    modifier onlyOwner() {
        if (msg.sender != owner) {
            revert OnlyOwner();
        }
        _;
    }

    modifier onlyOperator() {
        if (!operators[msg.sender]) {
            revert UnauthorizedOperator();
        }
        _;
    }

    constructor() {
        owner = msg.sender;
        operators[msg.sender] = true;
    }

    /**
     * @notice Submit a daily anchor
     * @param _date Date in YYYYMMDD format
     * @param _merkleRoot Merkle root of all moderation actions
     * @param _actionCount Number of actions included
     */
    function submitAnchor(
        uint256 _date,
        bytes32 _merkleRoot,
        uint256 _actionCount
    ) external onlyOperator {
        if (anchors[_date].timestamp != 0) {
            revert AnchorAlreadyExists();
        }

        anchors[_date] = Anchor({
            merkleRoot: _merkleRoot,
            actionCount: _actionCount,
            timestamp: block.timestamp,
            operator: msg.sender
        });

        emit AnchorSubmitted(_date, _merkleRoot, _actionCount, msg.sender);
    }

    /**
     * @notice Add an authorized operator
     * @param _operator Address to add
     */
    function addOperator(address _operator) external onlyOwner {
        if (_operator == address(0)) revert ZeroAddress();
        operators[_operator] = true;
        emit OperatorAdded(_operator);
    }

    /**
     * @notice Transfer ownership to a new address
     * @param _newOwner Address of the new owner
     */
    function transferOwnership(address _newOwner) external onlyOwner {
        if (_newOwner == address(0)) revert ZeroAddress();
        emit OwnershipTransferred(owner, _newOwner);
        owner = _newOwner;
    }

    /**
     * @notice Remove an operator
     * @param _operator Address to remove
     */
    function removeOperator(address _operator) external onlyOwner {
        operators[_operator] = false;
        emit OperatorRemoved(_operator);
    }

    /**
     * @notice Get anchor for a specific date
     * @param _date Date in YYYYMMDD format
     * @return Anchor struct
     */
    function getAnchor(uint256 _date) external view returns (Anchor memory) {
        return anchors[_date];
    }

    /**
     * @notice Verify a Merkle proof against a daily anchor
     * @param _date Date in YYYYMMDD format
     * @param _proof Merkle proof
     * @param _leaf Leaf to verify
     * @return bool indicating if proof is valid
     */
    function verifyProof(
        uint256 _date,
        bytes32[] calldata _proof,
        bytes32 _leaf
    ) external view returns (bool) {
        bytes32 computedHash = _leaf;

        for (uint256 i = 0; i < _proof.length; i++) {
            bytes32 proofElement = _proof[i];

            if (computedHash <= proofElement) {
                computedHash = keccak256(abi.encodePacked(computedHash, proofElement));
            } else {
                computedHash = keccak256(abi.encodePacked(proofElement, computedHash));
            }
        }

        return computedHash == anchors[_date].merkleRoot;
    }
}
