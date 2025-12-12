// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

contract ReputationSBT is ERC721, AccessControl {

    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER_ROLE");

    enum Tier { BRONZE, SILVER, GOLD, PLATINUM }

    struct ReputationData {
        uint256 score;
        Tier tier;
        uint256 totalReviews;
        uint256 accurateReviews;
        uint256 disputedReviews;
        uint256 mintedAt;
        uint256 lastUpdate;
        uint256 lastDecayApplied;
        bool isActive;
    }

    mapping(uint256 => ReputationData) public reputations;
    mapping(address => uint256) public walletToToken;

    uint256 private _nextTokenId = 1;
    string private _baseTokenURI;

    uint256 public constant BRONZE_THRESHOLD = 0;
    uint256 public constant SILVER_THRESHOLD = 100;
    uint256 public constant GOLD_THRESHOLD = 500;
    uint256 public constant PLATINUM_THRESHOLD = 1000;

    uint256 public constant ACCURATE_REVIEW_POINTS = 10;
    uint256 public constant DISPUTED_REVIEW_PENALTY = 20;
    uint256 public constant DECAY_RATE = 1;
    uint256 public constant DECAY_INTERVAL = 7 days;

    event ReputationMinted(address indexed to, uint256 indexed tokenId, Tier tier);
    event ReputationUpdated(uint256 indexed tokenId, uint256 newScore, Tier newTier);
    event ReputationRevoked(uint256 indexed tokenId);
    event DecayApplied(uint256 indexed tokenId, uint256 decayAmount, uint256 newScore);
    event TierChanged(uint256 indexed tokenId, Tier oldTier, Tier newTier);

    constructor(string memory baseURI) ERC721("COVERT Reputation", "CREP") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(MANAGER_ROLE, msg.sender);
        _baseTokenURI = baseURI;
    }

    function mint(address _to, uint256 _initialScore)
        external
        onlyRole(MINTER_ROLE)
        returns (uint256)
    {
        require(_to != address(0), "Cannot mint to zero address");
        require(walletToToken[_to] == 0, "Address already has reputation token");

        uint256 tokenId = _nextTokenId++;

        _mint(_to, tokenId);

        Tier tier = _calculateTier(_initialScore);

        reputations[tokenId] = ReputationData({
            score: _initialScore,
            tier: tier,
            totalReviews: 0,
            accurateReviews: 0,
            disputedReviews: 0,
            mintedAt: block.timestamp,
            lastUpdate: block.timestamp,
            lastDecayApplied: block.timestamp,
            isActive: true
        });

        walletToToken[_to] = tokenId;

        emit ReputationMinted(_to, tokenId, tier);

        return tokenId;
    }

    function updateReputation(
        uint256 _tokenId,
        bool _wasAccurate,
        bool _wasDisputed
    ) external onlyRole(MANAGER_ROLE) {
        require(_exists(_tokenId), "Token does not exist");
        require(reputations[_tokenId].isActive, "Reputation is not active");

        ReputationData storage rep = reputations[_tokenId];

        _applyDecayIfNeeded(_tokenId);

        rep.totalReviews++;

        if (_wasAccurate) {
            rep.accurateReviews++;
            rep.score += ACCURATE_REVIEW_POINTS;
        }

        if (_wasDisputed) {
            rep.disputedReviews++;
            if (rep.score >= DISPUTED_REVIEW_PENALTY) {
                rep.score -= DISPUTED_REVIEW_PENALTY;
            } else {
                rep.score = 0;
            }
        }

        Tier oldTier = rep.tier;
        Tier newTier = _calculateTier(rep.score);

        if (oldTier != newTier) {
            rep.tier = newTier;
            emit TierChanged(_tokenId, oldTier, newTier);
        }

        rep.lastUpdate = block.timestamp;

        emit ReputationUpdated(_tokenId, rep.score, rep.tier);
    }

    function applyDecay(uint256 _tokenId) external {
        require(_exists(_tokenId), "Token does not exist");
        _applyDecayIfNeeded(_tokenId);
    }

    function revokeReputation(uint256 _tokenId) external onlyRole(MANAGER_ROLE) {
        require(_exists(_tokenId), "Token does not exist");

        reputations[_tokenId].isActive = false;

        emit ReputationRevoked(_tokenId);
    }

    function getReputation(uint256 _tokenId) external view returns (ReputationData memory) {
        require(_exists(_tokenId), "Token does not exist");
        return reputations[_tokenId];
    }

    function getWalletReputation(address _wallet) external view returns (ReputationData memory) {
        uint256 tokenId = walletToToken[_wallet];
        require(tokenId != 0, "Wallet has no reputation token");
        return reputations[tokenId];
    }

    function getAccuracyRate(uint256 _tokenId) external view returns (uint256) {
        require(_exists(_tokenId), "Token does not exist");

        ReputationData memory rep = reputations[_tokenId];

        if (rep.totalReviews == 0) {
            return 0;
        }

        return (rep.accurateReviews * 100) / rep.totalReviews;
    }

    function getTierName(Tier _tier) public pure returns (string memory) {
        if (_tier == Tier.BRONZE) return "Bronze";
        if (_tier == Tier.SILVER) return "Silver";
        if (_tier == Tier.GOLD) return "Gold";
        if (_tier == Tier.PLATINUM) return "Platinum";
        return "Unknown";
    }

    function tokenURI(uint256 _tokenId) public view override returns (string memory) {
        require(_exists(_tokenId), "Token does not exist");

        ReputationData memory rep = reputations[_tokenId];

        string memory tierName = getTierName(rep.tier);

        return string(
            abi.encodePacked(
                _baseTokenURI,
                Strings.toString(_tokenId),
                "?tier=",
                tierName,
                "&score=",
                Strings.toString(rep.score)
            )
        );
    }

    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId,
        uint256 batchSize
    ) internal virtual override {
        require(
            from == address(0) || to == address(0),
            "Soul-bound: Transfer not allowed"
        );

        super._beforeTokenTransfer(from, to, tokenId, batchSize);
    }

    function _calculateTier(uint256 _score) internal pure returns (Tier) {
        if (_score >= PLATINUM_THRESHOLD) return Tier.PLATINUM;
        if (_score >= GOLD_THRESHOLD) return Tier.GOLD;
        if (_score >= SILVER_THRESHOLD) return Tier.SILVER;
        return Tier.BRONZE;
    }

    function _applyDecayIfNeeded(uint256 _tokenId) internal {
        ReputationData storage rep = reputations[_tokenId];

        uint256 timeSinceLastDecay = block.timestamp - rep.lastDecayApplied;

        if (timeSinceLastDecay >= DECAY_INTERVAL) {
            uint256 periods = timeSinceLastDecay / DECAY_INTERVAL;
            uint256 decayAmount = periods * DECAY_RATE;

            if (rep.score >= decayAmount) {
                rep.score -= decayAmount;
            } else {
                rep.score = 0;
            }

            Tier oldTier = rep.tier;
            Tier newTier = _calculateTier(rep.score);

            if (oldTier != newTier) {
                rep.tier = newTier;
                emit TierChanged(_tokenId, oldTier, newTier);
            }

            rep.lastDecayApplied = block.timestamp;

            emit DecayApplied(_tokenId, decayAmount, rep.score);
        }
    }

    function supportsInterface(bytes4 interfaceId)
        public
        view
        override(ERC721, AccessControl)
        returns (bool)
    {
        return super.supportsInterface(interfaceId);
    }
}
