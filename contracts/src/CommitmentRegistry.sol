// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CommitmentRegistry
 * @notice Stores tamper-proof commitments of encrypted reports on-chain
 * @dev This contract is the core of C.O.V.E.R.T's immutability guarantee
 */
contract CommitmentRegistry {
    /// @notice Represents a commitment to a report
    struct Commitment {
        bytes32 cidHash;        // Hash of IPFS CID (privacy layer)
        uint8 visibility;       // 0=private, 1=moderated, 2=public
        address submitter;      // Burner wallet address
        uint256 timestamp;      // Block timestamp
        bool isActive;          // Deletion flag
    }

    /// @notice Mapping from CID hash to commitment
    mapping(bytes32 => Commitment) public commitments;

    /// @notice Event emitted when a new report is committed
    event ReportCommitted(
        bytes32 indexed cidHash,
        address indexed submitter,
        uint8 visibility,
        uint256 timestamp
    );

    /// @notice Event emitted when a report is marked inactive
    event ReportDeactivated(bytes32 indexed cidHash, address indexed submitter);

    /// @notice Errors
    error CommitmentAlreadyExists();
    error CommitmentNotFound();
    error UnauthorizedDeactivation();

    /**
     * @notice Submit a new report commitment
     * @param _cidHash Hash of the IPFS CID
     * @param _visibility Visibility level (0=private, 1=moderated, 2=public)
     */
    function commit(bytes32 _cidHash, uint8 _visibility) external {
        if (commitments[_cidHash].timestamp != 0) {
            revert CommitmentAlreadyExists();
        }

        commitments[_cidHash] = Commitment({
            cidHash: _cidHash,
            visibility: _visibility,
            submitter: msg.sender,
            timestamp: block.timestamp,
            isActive: true
        });

        emit ReportCommitted(_cidHash, msg.sender, _visibility, block.timestamp);
    }

    /**
     * @notice Deactivate a report (mark as deleted, but keep on-chain)
     * @param _cidHash Hash of the IPFS CID
     */
    function deactivate(bytes32 _cidHash) external {
        Commitment storage commitment = commitments[_cidHash];

        if (commitment.timestamp == 0) {
            revert CommitmentNotFound();
        }

        if (commitment.submitter != msg.sender) {
            revert UnauthorizedDeactivation();
        }

        commitment.isActive = false;

        emit ReportDeactivated(_cidHash, msg.sender);
    }

    /**
     * @notice Get commitment details
     * @param _cidHash Hash of the IPFS CID
     * @return Commitment struct
     */
    function getCommitment(bytes32 _cidHash) external view returns (Commitment memory) {
        return commitments[_cidHash];
    }

    /**
     * @notice Verify if a commitment exists and is active
     * @param _cidHash Hash of the IPFS CID
     * @return bool indicating if commitment exists and is active
     */
    function isActive(bytes32 _cidHash) external view returns (bool) {
        return commitments[_cidHash].isActive;
    }
}
