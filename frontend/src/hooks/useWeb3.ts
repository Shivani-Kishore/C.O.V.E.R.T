/**
 * C.O.V.E.R.T - useWeb3 Hook
 *
 * React hook for Web3 wallet connection and blockchain interactions.
 *
 * Session persistence strategy
 * ─────────────────────────────
 * Wallet state is stored in a Zustand store (walletSessionStore) that is
 * persisted to localStorage with a 24-hour expiry.
 *
 * On page load:
 *   1. The store is hydrated instantly from localStorage (no flash).
 *   2. A silent background check (eth_accounts, no popup) confirms MetaMask
 *      still has permission and updates balance/chainId.
 *   3. If MetaMask has revoked permission or the session expired, the store
 *      is cleared quietly.
 *
 * The wallet is disconnected ONLY when:
 *   • The user explicitly clicks "Disconnect".
 *   • The 24-hour session window expires (checked on every page load).
 *   • MetaMask fires accountsChanged with an empty list.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { web3Service, WalletType, TransactionResult, Commitment } from '../services/web3';
import { useWalletSessionStore } from '../stores/walletSessionStore';
import { protocolService } from '../services/protocol';
import { useCovBalanceStore } from '../stores/covBalanceStore';
import type { WalletState } from '../services/web3';

const API_BASE = import.meta.env.VITE_API_URL || '';

/**
 * Perform SIWE authentication: fetch nonce, sign message, verify with backend, store JWT.
 */
async function authenticateWithSIWE(address: string): Promise<void> {
  try {
    // 1. Get nonce
    const nonceRes = await fetch(`${API_BASE}/api/v1/auth/nonce?address=${address}`);
    if (!nonceRes.ok) throw new Error('Failed to fetch nonce');
    const { nonce } = await nonceRes.json();

    // 2. Build SIWE message
    const domain = window.location.host;
    const origin = window.location.origin;
    const issuedAt = new Date().toISOString();
    const message = [
      `${domain} wants you to sign in with your Ethereum account:`,
      address,
      '',
      'Sign in to C.O.V.E.R.T',
      '',
      `URI: ${origin}`,
      'Version: 1',
      `Chain ID: ${parseInt(import.meta.env.VITE_CHAIN_ID || '84532')}`,
      `Nonce: ${nonce}`,
      `Issued At: ${issuedAt}`,
    ].join('\n');

    // 3. Sign with wallet
    const signature = await web3Service.signMessage(message);

    // 4. Verify with backend
    const verifyRes = await fetch(`${API_BASE}/api/v1/auth/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, signature }),
    });
    if (!verifyRes.ok) {
      const err = await verifyRes.json().catch(() => ({ detail: 'Verification failed' }));
      throw new Error(err.detail || 'SIWE verification failed');
    }

    const { token } = await verifyRes.json();
    localStorage.setItem('token', token);
  } catch (err) {
    console.error('[SIWE] Authentication failed:', err);
    // Don't block wallet connection — just log the error.
    // Authenticated endpoints will prompt re-auth if needed.
  }
}

interface UseWeb3Return {
  walletState: WalletState;
  isConnecting: boolean;
  error: string | null;

  connect: (walletType?: WalletType) => Promise<void>;
  disconnect: () => void;
  switchNetwork: (chainId: number) => Promise<void>;

  commitReport: (cid: string, visibility: number) => Promise<TransactionResult>;
  getCommitment: (cidHash: string) => Promise<Commitment | null>;
  verifyCommitment: (cidHash: string) => Promise<boolean>;
  deactivateReport: (cidHash: string) => Promise<TransactionResult>;

  signMessage: (message: string) => Promise<string>;
  computeCidHash: (cid: string) => string;
}

export function useWeb3(): UseWeb3Return {
  const session = useWalletSessionStore();
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Derive WalletState from the shared store.
  // Memoized so the object reference only changes when actual values change —
  // prevents downstream effects from re-firing on unrelated store updates
  // (e.g. expiresAt bumping on every silent session restore).
  const sessionValid = session.isSessionValid();
  const walletState: WalletState = useMemo(() => ({
    connected: session.connected && sessionValid,
    address: sessionValid ? session.address : null,
    chainId: sessionValid ? session.chainId : null,
    balance: sessionValid ? session.balance : null,
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }), [session.connected, sessionValid, session.address, session.chainId, session.balance]);

  // ── Configure contracts once on mount ─────────────────────────────────────
  useEffect(() => {
    const config = {
      commitmentRegistryAddress: import.meta.env.VITE_COMMITMENT_REGISTRY_ADDRESS || '',
      dailyAnchorAddress: import.meta.env.VITE_DAILY_ANCHOR_ADDRESS || '',
    };
    if (config.commitmentRegistryAddress) {
      web3Service.configure(config);
    }

    // Configure protocol service
    const protocolConfig = {
      covCreditsAddress: import.meta.env.VITE_COV_CREDITS_ADDRESS || '',
      covertBadgesAddress: import.meta.env.VITE_COVERT_BADGES_ADDRESS || '',
      covertProtocolAddress: import.meta.env.VITE_COVERT_PROTOCOL_ADDRESS || '',
    };
    import('../services/protocol').then(({ protocolService }) => {
      protocolService.configure(protocolConfig);
    });
  }, []);

  // ── Silent session restore on page load ───────────────────────────────────
  useEffect(() => {
    const restore = async () => {
      if (!window.ethereum) return;

      // If session expired or user deliberately disconnected, do nothing
      if (!session.isSessionValid()) {
        if (session.connected) {
          // Session was valid last time but has since expired — clean up
          session.clearSession();
        }
        return;
      }

      try {
        // getWalletStateSilent re-initializes the ethers provider from existing
        // permissions (eth_accounts) without triggering a MetaMask popup
        const state = await web3Service.getWalletStateSilent();
        if (state.connected && state.address) {
          session.saveSession(state.address, state.chainId, state.balance);
        } else {
          // MetaMask has no accounts / permission revoked — clear the stale session
          session.clearSession();
        }
      } catch (err) {
        console.error('[useWeb3] session restore failed:', err);
        // Don't clear on transient error — keep stored state so next load can retry
      }
    };

    restore();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // run once on mount

  // ── MetaMask event listeners ───────────────────────────────────────────────
  useEffect(() => {
    if (!window.ethereum) return;

    const handleAccountsChanged = async (accounts: unknown) => {
      const list = accounts as string[];
      if (list.length === 0) {
        // User switched to "no account" or locked MetaMask
        session.clearSession();
      } else {
        try {
          const state = await web3Service.getWalletStateSilent();
          if (state.connected && state.address) {
            session.saveSession(state.address, state.chainId, state.balance);
          }
        } catch (err) {
          console.error('[useWeb3] accountsChanged handler failed:', err);
        }
      }
    };

    const handleChainChanged = async () => {
      try {
        const state = await web3Service.getWalletStateSilent();
        if (state.connected) {
          session.updateSession({ chainId: state.chainId, balance: state.balance });
        }
      } catch (err) {
        console.error('[useWeb3] chainChanged handler failed:', err);
      }
    };

    window.ethereum.on('accountsChanged', handleAccountsChanged);
    window.ethereum.on('chainChanged', handleChainChanged);

    return () => {
      window.ethereum?.removeListener('accountsChanged', handleAccountsChanged);
      window.ethereum?.removeListener('chainChanged', handleChainChanged);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Connect ────────────────────────────────────────────────────────────────
  const connect = useCallback(async (walletType: WalletType = 'metamask') => {
    setIsConnecting(true);
    setError(null);

    const wasLoggedOut = session.deliberatelyDisconnected;

    try {
      const state = await web3Service.connect(walletType, wasLoggedOut);
      if (state.address) {
        session.saveSession(state.address, state.chainId, state.balance);
        // Authenticate with backend via SIWE to get a JWT
        await authenticateWithSIWE(state.address);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect wallet';
      setError(message);
      throw err;
    } finally {
      setIsConnecting(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session.deliberatelyDisconnected]);

  // ── Disconnect ─────────────────────────────────────────────────────────────
  const disconnect = useCallback(() => {
    // Best-effort: revoke MetaMask site permissions (EIP-2255)
    window.ethereum
      ?.request({
        method: 'wallet_revokePermissions',
        params: [{ eth_accounts: {} }],
      })
      .catch(() => { });

    web3Service.disconnect();
    session.clearSession();
    localStorage.removeItem('token');
    setError(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Switch network ─────────────────────────────────────────────────────────
  const switchNetwork = useCallback(async (chainId: number) => {
    try {
      await web3Service.switchNetwork(chainId);
      const state = await web3Service.getWalletState();
      if (state.connected) {
        session.updateSession({ chainId: state.chainId, balance: state.balance });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to switch network';
      setError(message);
      throw err;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Contract interactions ──────────────────────────────────────────────────
  const commitReport = useCallback(
    async (cid: string, visibility: number): Promise<TransactionResult> => {
      if (!walletState.connected) throw new Error('Wallet not connected');
      const cidHash = web3Service.computeCidHash(cid);

      // ── Dev-mode fast path ─────────────────────────────────────────────────
      // When VITE_DEV_MODE=true, skip ALL real blockchain interaction regardless
      // of whether contract addresses are configured. This avoids MetaMask
      // popups, gas fees, and contract-call errors during local development.
      if (import.meta.env.VITE_DEV_MODE === 'true') {
        console.warn(
          '[DEV MODE] Skipping real blockchain commit — using simulated tx hash. ' +
          'Set VITE_DEV_MODE=false to send real transactions.'
        );
        const hashBuffer = await crypto.subtle.digest(
          'SHA-256',
          new TextEncoder().encode(`tx-${cidHash}-${Date.now()}`)
        );
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const fakeTxHash = '0x' + hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
        return { success: true, transactionHash: fakeTxHash, hash: fakeTxHash, blockNumber: 1, status: 'success' };
      }
      // ──────────────────────────────────────────────────────────────────────

      // Use CovertProtocol.createReport() when the protocol contract is configured.
      // This is required so reports appear on-chain in the reviewer/moderator queue.
      // Form visibility: 0=private, 1=moderated, 2=public
      // Contract Visibility enum: PUBLIC=0, PRIVATE=1
      if (import.meta.env.VITE_COVERT_PROTOCOL_ADDRESS) {
        const protocolVisibility = visibility === 2 ? 0 : 1;
        await protocolService.connect();

        // Auto-claim the one-time 30 COV welcome grant if the user hasn't claimed yet.
        // New wallets have 0 COV; without this they get InsufficientCredits on createReport.
        if (walletState.address) {
          const userState = await protocolService.getUserState(walletState.address);
          // Always sync on-chain balance to the store so the profile UI shows the real value
          useCovBalanceStore.getState().setBalance(walletState.address, parseFloat(userState.covBalance));

          if (!userState.welcomeClaimed) {
            await protocolService.claimWelcome();
            // After claim, balance is 30 COV — sync that too
            useCovBalanceStore.getState().setBalance(walletState.address, 30);
          } else {
            // Already claimed — verify balance is sufficient before sending the TX.
            // PUBLIC report = 10 COV, PRIVATE/moderated = 6 COV.
            const requiredStake = protocolVisibility === 0 ? 10 : 6;
            const covBalance = parseFloat(userState.covBalance);
            if (covBalance < requiredStake) {
              throw new Error(
                `Insufficient COV credits. You need ${requiredStake} COV to submit this report ` +
                `but your current balance is ${covBalance.toFixed(2)} COV. ` +
                `COV is returned when your reports are reviewed and finalized.`
              );
            }
          }
        }

        let txHash: string;
        try {
          txHash = await protocolService.createReport(protocolVisibility, cidHash);
        } catch (err) {
          // Decode the InsufficientCredits() custom error (selector 0x43fb9453)
          const errStr = err instanceof Error ? err.message : String(err);
          if (errStr.includes('0x43fb9453') || errStr.toLowerCase().includes('insufficientcredits')) {
            throw new Error(
              'Insufficient COV credits to submit this report. ' +
              'Your COV balance may have been spent on previous submissions or stakes. ' +
              'COV is returned when reports are finalized.'
            );
          }
          throw err;
        }
        return { success: true, transactionHash: txHash, hash: txHash, blockNumber: 0, status: 'success' };
      }

      // Fallback: CommitmentRegistry or dev-mode simulation
      return web3Service.commitReport(cidHash, visibility);
    },
    [walletState.connected, walletState.address]
  );

  const getCommitment = useCallback(
    (cidHash: string): Promise<Commitment | null> => web3Service.getCommitment(cidHash),
    []
  );

  const verifyCommitment = useCallback(
    (cidHash: string): Promise<boolean> => web3Service.verifyCommitment(cidHash),
    []
  );

  const deactivateReport = useCallback(
    async (cidHash: string): Promise<TransactionResult> => {
      if (!walletState.connected) throw new Error('Wallet not connected');
      return web3Service.deactivateReport(cidHash);
    },
    [walletState.connected]
  );

  const signMessage = useCallback(
    async (message: string): Promise<string> => {
      if (!walletState.connected) throw new Error('Wallet not connected');
      return web3Service.signMessage(message);
    },
    [walletState.connected]
  );

  const computeCidHash = useCallback(
    (cid: string): string => web3Service.computeCidHash(cid),
    []
  );

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
