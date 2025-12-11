/**
 * C.O.V.E.R.T - useWeb3 Hook
 *
 * React hook for Web3 wallet connection and blockchain interactions
 */

import { useState, useEffect, useCallback } from 'react';
import { web3Service, WalletState, WalletType, TransactionResult, Commitment } from '../services/web3';

interface UseWeb3Return {
  // State
  walletState: WalletState;
  isConnecting: boolean;
  error: string | null;

  // Actions
  connect: (walletType?: WalletType) => Promise<void>;
  disconnect: () => void;
  switchNetwork: (chainId: number) => Promise<void>;

  // Contract interactions
  commitReport: (cid: string, visibility: number) => Promise<TransactionResult>;
  getCommitment: (cidHash: string) => Promise<Commitment | null>;
  verifyCommitment: (cidHash: string) => Promise<boolean>;
  deactivateReport: (cidHash: string) => Promise<TransactionResult>;

  // Utilities
  signMessage: (message: string) => Promise<string>;
  computeCidHash: (cid: string) => string;
}

const initialWalletState: WalletState = {
  connected: false,
  address: null,
  chainId: null,
  balance: null,
};

/**
 * Custom hook for Web3 interactions
 */
export function useWeb3(): UseWeb3Return {
  const [walletState, setWalletState] = useState<WalletState>(initialWalletState);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Configure web3 service on mount
  useEffect(() => {
    const config = {
      commitmentRegistryAddress: import.meta.env.VITE_COMMITMENT_REGISTRY_ADDRESS || '',
      dailyAnchorAddress: import.meta.env.VITE_DAILY_ANCHOR_ADDRESS || '',
    };

    if (config.commitmentRegistryAddress) {
      web3Service.configure(config);
    }
  }, []);

  // Listen for account changes
  useEffect(() => {
    if (!window.ethereum) return;

    const handleAccountsChanged = async (accounts: unknown) => {
      const accountList = accounts as string[];
      if (accountList.length === 0) {
        setWalletState(initialWalletState);
      } else {
        try {
          const state = await web3Service.getWalletState();
          setWalletState(state);
        } catch (err) {
          console.error('Failed to update wallet state:', err);
        }
      }
    };

    const handleChainChanged = async () => {
      try {
        const state = await web3Service.getWalletState();
        setWalletState(state);
      } catch (err) {
        console.error('Failed to update on chain change:', err);
      }
    };

    window.ethereum.on('accountsChanged', handleAccountsChanged);
    window.ethereum.on('chainChanged', handleChainChanged);

    return () => {
      window.ethereum?.removeListener('accountsChanged', handleAccountsChanged);
      window.ethereum?.removeListener('chainChanged', handleChainChanged);
    };
  }, []);

  // Check for existing connection on mount
  useEffect(() => {
    const checkConnection = async () => {
      if (!window.ethereum) return;

      try {
        const accounts = (await window.ethereum.request({
          method: 'eth_accounts',
        })) as string[];

        if (accounts.length > 0) {
          const state = await web3Service.connect();
          setWalletState(state);
        }
      } catch (err) {
        console.error('Failed to check connection:', err);
      }
    };

    checkConnection();
  }, []);

  /**
   * Connect wallet
   */
  const connect = useCallback(async (walletType: WalletType = 'metamask') => {
    setIsConnecting(true);
    setError(null);

    try {
      const state = await web3Service.connect(walletType);
      setWalletState(state);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect wallet';
      setError(message);
      throw err;
    } finally {
      setIsConnecting(false);
    }
  }, []);

  /**
   * Disconnect wallet
   */
  const disconnect = useCallback(() => {
    web3Service.disconnect();
    setWalletState(initialWalletState);
    setError(null);
  }, []);

  /**
   * Switch network
   */
  const switchNetwork = useCallback(async (chainId: number) => {
    try {
      await web3Service.switchNetwork(chainId);
      const state = await web3Service.getWalletState();
      setWalletState(state);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to switch network';
      setError(message);
      throw err;
    }
  }, []);

  /**
   * Commit a report to the blockchain
   */
  const commitReport = useCallback(
    async (cid: string, visibility: number): Promise<TransactionResult> => {
      if (!walletState.connected) {
        throw new Error('Wallet not connected');
      }

      const cidHash = web3Service.computeCidHash(cid);
      return await web3Service.commitReport(cidHash, visibility);
    },
    [walletState.connected]
  );

  /**
   * Get commitment details
   */
  const getCommitment = useCallback(
    async (cidHash: string): Promise<Commitment | null> => {
      return await web3Service.getCommitment(cidHash);
    },
    []
  );

  /**
   * Verify commitment is active
   */
  const verifyCommitment = useCallback(async (cidHash: string): Promise<boolean> => {
    return await web3Service.verifyCommitment(cidHash);
  }, []);

  /**
   * Deactivate a report
   */
  const deactivateReport = useCallback(
    async (cidHash: string): Promise<TransactionResult> => {
      if (!walletState.connected) {
        throw new Error('Wallet not connected');
      }
      return await web3Service.deactivateReport(cidHash);
    },
    [walletState.connected]
  );

  /**
   * Sign a message
   */
  const signMessage = useCallback(
    async (message: string): Promise<string> => {
      if (!walletState.connected) {
        throw new Error('Wallet not connected');
      }
      return await web3Service.signMessage(message);
    },
    [walletState.connected]
  );

  /**
   * Compute CID hash
   */
  const computeCidHash = useCallback((cid: string): string => {
    return web3Service.computeCidHash(cid);
  }, []);

  return {
    walletState,
    isConnecting,
    error,
    connect,
    disconnect,
    switchNetwork,
    commitReport,
    getCommitment,
    verifyCommitment,
    deactivateReport,
    signMessage,
    computeCidHash,
  };
}

export default useWeb3;
