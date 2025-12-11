/**
 * C.O.V.E.R.T - Web3 Service
 *
 * Handles wallet connections and contract interactions
 */

import { ethers, BrowserProvider, Signer, Contract, ContractTransactionResponse } from 'ethers';

// Contract ABIs (minimal interfaces)
const COMMITMENT_REGISTRY_ABI = [
  'function commit(bytes32 _cidHash, uint8 _visibility) external',
  'function deactivate(bytes32 _cidHash) external',
  'function getCommitment(bytes32 _cidHash) external view returns (tuple(bytes32 cidHash, uint8 visibility, address submitter, uint256 timestamp, bool isActive))',
  'function isActive(bytes32 _cidHash) external view returns (bool)',
  'event ReportCommitted(bytes32 indexed cidHash, address indexed submitter, uint8 visibility, uint256 timestamp)',
  'event ReportDeactivated(bytes32 indexed cidHash, address indexed submitter)',
];

const DAILY_ANCHOR_ABI = [
  'function submitAnchor(uint256 _date, bytes32 _merkleRoot, uint256 _actionCount) external',
  'function getAnchor(uint256 _date) external view returns (tuple(bytes32 merkleRoot, uint256 actionCount, uint256 timestamp, address operator))',
  'function verifyProof(uint256 _date, bytes32[] calldata _proof, bytes32 _leaf) external view returns (bool)',
  'function operators(address) external view returns (bool)',
  'event AnchorSubmitted(uint256 indexed date, bytes32 merkleRoot, uint256 actionCount, address operator)',
];

// Types
export interface Commitment {
  cidHash: string;
  visibility: number;
  submitter: string;
  timestamp: number;
  isActive: boolean;
}

export interface Anchor {
  merkleRoot: string;
  actionCount: number;
  timestamp: number;
  operator: string;
}

export interface TransactionResult {
  hash: string;
  blockNumber: number;
  status: 'success' | 'failed';
  gasUsed: bigint;
}

export interface Web3ServiceConfig {
  commitmentRegistryAddress: string;
  dailyAnchorAddress: string;
  rpcUrl?: string;
}

export type WalletType = 'metamask' | 'walletconnect' | 'coinbase';

export interface WalletState {
  connected: boolean;
  address: string | null;
  chainId: number | null;
  balance: string | null;
}

/**
 * Web3 Service for C.O.V.E.R.T
 */
class Web3Service {
  private provider: BrowserProvider | null = null;
  private signer: Signer | null = null;
  private commitmentRegistry: Contract | null = null;
  private dailyAnchor: Contract | null = null;
  private config: Web3ServiceConfig | null = null;

  /**
   * Configure the service with contract addresses
   */
  configure(config: Web3ServiceConfig): void {
    this.config = config;
  }

  /**
   * Connect to wallet
   */
  async connect(walletType: WalletType = 'metamask'): Promise<WalletState> {
    if (!window.ethereum) {
      throw new Error('No Web3 provider found. Please install MetaMask.');
    }

    try {
      // Request account access
      await window.ethereum.request({ method: 'eth_requestAccounts' });

      this.provider = new BrowserProvider(window.ethereum);
      this.signer = await this.provider.getSigner();

      const address = await this.signer.getAddress();
      const network = await this.provider.getNetwork();
      const balance = await this.provider.getBalance(address);

      // Initialize contracts
      if (this.config) {
        this.commitmentRegistry = new Contract(
          this.config.commitmentRegistryAddress,
          COMMITMENT_REGISTRY_ABI,
          this.signer
        );
        this.dailyAnchor = new Contract(
          this.config.dailyAnchorAddress,
          DAILY_ANCHOR_ABI,
          this.signer
        );
      }

      return {
        connected: true,
        address,
        chainId: Number(network.chainId),
        balance: ethers.formatEther(balance),
      };
    } catch (error) {
      console.error('Failed to connect wallet:', error);
      throw error;
    }
  }

  /**
   * Disconnect wallet
   */
  disconnect(): void {
    this.provider = null;
    this.signer = null;
    this.commitmentRegistry = null;
    this.dailyAnchor = null;
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.signer !== null;
  }

  /**
   * Get current wallet state
   */
  async getWalletState(): Promise<WalletState> {
    if (!this.provider || !this.signer) {
      return {
        connected: false,
        address: null,
        chainId: null,
        balance: null,
      };
    }

    const address = await this.signer.getAddress();
    const network = await this.provider.getNetwork();
    const balance = await this.provider.getBalance(address);

    return {
      connected: true,
      address,
      chainId: Number(network.chainId),
      balance: ethers.formatEther(balance),
    };
  }

  /**
   * Switch to a different network
   */
  async switchNetwork(chainId: number): Promise<void> {
    if (!window.ethereum) throw new Error('No provider');

    try {
      await window.ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: `0x${chainId.toString(16)}` }],
      });
    } catch (error: unknown) {
      // Chain not added, try to add it
      if ((error as { code?: number })?.code === 4902) {
        await this.addNetwork(chainId);
      } else {
        throw error;
      }
    }
  }

  /**
   * Add a network to wallet
   */
  private async addNetwork(chainId: number): Promise<void> {
    const networks: Record<number, object> = {
      8453: {
        chainId: '0x2105',
        chainName: 'Base',
        nativeCurrency: { name: 'ETH', symbol: 'ETH', decimals: 18 },
        rpcUrls: ['https://mainnet.base.org'],
        blockExplorerUrls: ['https://basescan.org'],
      },
      84532: {
        chainId: '0x14a34',
        chainName: 'Base Sepolia',
        nativeCurrency: { name: 'ETH', symbol: 'ETH', decimals: 18 },
        rpcUrls: ['https://sepolia.base.org'],
        blockExplorerUrls: ['https://sepolia.basescan.org'],
      },
      31337: {
        chainId: '0x7a69',
        chainName: 'Localhost',
        nativeCurrency: { name: 'ETH', symbol: 'ETH', decimals: 18 },
        rpcUrls: ['http://localhost:8545'],
      },
    };

    const networkParams = networks[chainId];
    if (!networkParams) throw new Error(`Unknown network: ${chainId}`);

    await window.ethereum.request({
      method: 'wallet_addEthereumChain',
      params: [networkParams],
    });
  }

  // ============ CommitmentRegistry Functions ============

  /**
   * Submit a report commitment
   */
  async commitReport(
    cidHash: string,
    visibility: number
  ): Promise<TransactionResult> {
    if (!this.commitmentRegistry) {
      throw new Error('Contract not initialized');
    }

    try {
      // Estimate gas
      const gasEstimate = await this.commitmentRegistry.commit.estimateGas(
        cidHash,
        visibility
      );

      // Send transaction with 20% gas buffer
      const tx: ContractTransactionResponse = await this.commitmentRegistry.commit(
        cidHash,
        visibility,
        { gasLimit: (gasEstimate * 120n) / 100n }
      );

      console.log('Transaction sent:', tx.hash);

      // Wait for confirmation
      const receipt = await tx.wait();

      if (!receipt) throw new Error('Transaction failed');

      return {
        hash: receipt.hash,
        blockNumber: receipt.blockNumber,
        status: receipt.status === 1 ? 'success' : 'failed',
        gasUsed: receipt.gasUsed,
      };
    } catch (error) {
      console.error('Commit failed:', error);
      throw error;
    }
  }

  /**
   * Get commitment details
   */
  async getCommitment(cidHash: string): Promise<Commitment | null> {
    if (!this.commitmentRegistry) {
      throw new Error('Contract not initialized');
    }

    try {
      const result = await this.commitmentRegistry.getCommitment(cidHash);
      return {
        cidHash: result.cidHash,
        visibility: Number(result.visibility),
        submitter: result.submitter,
        timestamp: Number(result.timestamp),
        isActive: result.isActive,
      };
    } catch {
      return null;
    }
  }

  /**
   * Verify if a commitment is active
   */
  async verifyCommitment(cidHash: string): Promise<boolean> {
    if (!this.commitmentRegistry) {
      throw new Error('Contract not initialized');
    }

    try {
      return await this.commitmentRegistry.isActive(cidHash);
    } catch {
      return false;
    }
  }

  /**
   * Deactivate a report
   */
  async deactivateReport(cidHash: string): Promise<TransactionResult> {
    if (!this.commitmentRegistry) {
      throw new Error('Contract not initialized');
    }

    const tx = await this.commitmentRegistry.deactivate(cidHash);
    const receipt = await tx.wait();

    if (!receipt) throw new Error('Transaction failed');

    return {
      hash: receipt.hash,
      blockNumber: receipt.blockNumber,
      status: receipt.status === 1 ? 'success' : 'failed',
      gasUsed: receipt.gasUsed,
    };
  }

  // ============ DailyAnchor Functions ============

  /**
   * Submit a daily anchor
   */
  async submitAnchor(
    date: number,
    merkleRoot: string,
    actionCount: number
  ): Promise<TransactionResult> {
    if (!this.dailyAnchor) {
      throw new Error('Contract not initialized');
    }

    const tx = await this.dailyAnchor.submitAnchor(date, merkleRoot, actionCount);
    const receipt = await tx.wait();

    if (!receipt) throw new Error('Transaction failed');

    return {
      hash: receipt.hash,
      blockNumber: receipt.blockNumber,
      status: receipt.status === 1 ? 'success' : 'failed',
      gasUsed: receipt.gasUsed,
    };
  }

  /**
   * Get anchor for a date
   */
  async getAnchor(date: number): Promise<Anchor | null> {
    if (!this.dailyAnchor) {
      throw new Error('Contract not initialized');
    }

    try {
      const result = await this.dailyAnchor.getAnchor(date);
      if (result.timestamp === 0n) return null;
      return {
        merkleRoot: result.merkleRoot,
        actionCount: Number(result.actionCount),
        timestamp: Number(result.timestamp),
        operator: result.operator,
      };
    } catch {
      return null;
    }
  }

  /**
   * Verify a merkle proof
   */
  async verifyProof(
    date: number,
    proof: string[],
    leaf: string
  ): Promise<boolean> {
    if (!this.dailyAnchor) {
      throw new Error('Contract not initialized');
    }

    return await this.dailyAnchor.verifyProof(date, proof, leaf);
  }

  // ============ Event Listeners ============

  /**
   * Listen for new report commitments
   */
  onReportCommitted(
    callback: (cidHash: string, submitter: string, visibility: number, timestamp: number) => void
  ): void {
    if (!this.commitmentRegistry) return;

    this.commitmentRegistry.on(
      'ReportCommitted',
      (cidHash, submitter, visibility, timestamp) => {
        callback(cidHash, submitter, Number(visibility), Number(timestamp));
      }
    );
  }

  /**
   * Listen for anchor submissions
   */
  onAnchorSubmitted(
    callback: (date: number, merkleRoot: string, actionCount: number, operator: string) => void
  ): void {
    if (!this.dailyAnchor) return;

    this.dailyAnchor.on(
      'AnchorSubmitted',
      (date, merkleRoot, actionCount, operator) => {
        callback(Number(date), merkleRoot, Number(actionCount), operator);
      }
    );
  }

  /**
   * Remove all event listeners
   */
  removeAllListeners(): void {
    this.commitmentRegistry?.removeAllListeners();
    this.dailyAnchor?.removeAllListeners();
  }

  // ============ Utility Functions ============

  /**
   * Compute CID hash for commitment
   */
  computeCidHash(cid: string): string {
    return ethers.keccak256(ethers.toUtf8Bytes(cid));
  }

  /**
   * Sign a message with the connected wallet
   */
  async signMessage(message: string): Promise<string> {
    if (!this.signer) {
      throw new Error('Wallet not connected');
    }
    return await this.signer.signMessage(message);
  }

  /**
   * Get current block number
   */
  async getBlockNumber(): Promise<number> {
    if (!this.provider) {
      throw new Error('Provider not initialized');
    }
    return await this.provider.getBlockNumber();
  }
}

// Singleton instance
export const web3Service = new Web3Service();

export default web3Service;

// Type augmentation for window.ethereum
declare global {
  interface Window {
    ethereum?: {
      request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
      on: (event: string, callback: (...args: unknown[]) => void) => void;
      removeListener: (event: string, callback: (...args: unknown[]) => void) => void;
      isMetaMask?: boolean;
    };
  }
}
