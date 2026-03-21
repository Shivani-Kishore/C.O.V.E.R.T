import { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { useWeb3 } from './useWeb3';
import { protocolService } from '@/services/protocol';
import { BadgeType } from '@/types/protocol';
import { getAddressRole } from '@/config/roles';
import { useCovBalanceStore } from '@/stores/covBalanceStore';
import { API_BASE } from '@/config';

interface RoleAccessState {
  loading: boolean;
  isReviewer: boolean;
  isModerator: boolean;
  covBalance: string;
  lockedBalance: string;
  badges: { type: BadgeType; active: boolean; tokenId: string }[];
  reputationScore: number;
  reputationTier: string;
}

const INITIAL: RoleAccessState = {
  loading: true,
  isReviewer: false,
  isModerator: false,
  covBalance: '0',
  lockedBalance: '0',
  badges: [],
  reputationScore: 0,
  reputationTier: 'user',
};

async function fetchReputation(address: string): Promise<{ reputation_score: number; tier: string }> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/reputation/wallet/${address}`);
    if (!res.ok) return { reputation_score: 0, tier: 'user' };
    return await res.json();
  } catch {
    return { reputation_score: 0, tier: 'user' };
  }
}

export function useRoleAccess() {
  const { walletState } = useWeb3();
  const [state, setState] = useState<RoleAccessState>(INITIAL);
  // Live COV balance from the persistent store (updates immediately on stake/reward)
  const covBalanceLive = useCovBalanceStore(
    (s) => walletState.address ? s.getBalance(walletState.address) : 0
  );

  useEffect(() => {
    let cancelled = false;

    const loadRoles = async () => {
      if (!walletState.connected || !walletState.address) {
        setState({ ...INITIAL, loading: false });
        return;
      }

      protocolService.configure({
        covCreditsAddress: import.meta.env.VITE_COV_CREDITS_ADDRESS || '',
        covertBadgesAddress: import.meta.env.VITE_COVERT_BADGES_ADDRESS || '',
        covertProtocolAddress: import.meta.env.VITE_COVERT_PROTOCOL_ADDRESS || '',
      });

      setState((prev) => ({ ...prev, loading: true }));

      try {
        if (import.meta.env.VITE_DEV_MODE === 'true') {
          const role = getAddressRole(walletState.address);
          console.info(`[DEV MODE] Address ${walletState.address} → role: ${role}`);
          // Fetch real rep from backend so rep starts at 0 and reflects actual moderation outcomes
          const repData = await fetchReputation(walletState.address);

          // If CovertProtocol is deployed, sync the real on-chain COV balance into the store
          // so the UI always shows what the chain actually holds, not a stale localStorage value.
          if (import.meta.env.VITE_COVERT_PROTOCOL_ADDRESS) {
            try {
              await protocolService.connect();
              const userState = await protocolService.getUserState(walletState.address);
              const onChainBal = parseFloat(userState.covBalance);
              useCovBalanceStore.getState().setBalance(walletState.address, onChainBal);
            } catch {
              // Contract not reachable in this dev session — store balance stays as-is
            }
          }

          if (!cancelled) {
            setState({
              loading: false,
              isReviewer: role === 'reviewer',
              isModerator: role === 'moderator',
              covBalance: '0', // overridden by covBalanceLive from store below
              lockedBalance: '0',
              badges: [],
              reputationScore: repData.reputation_score,
              reputationTier: repData.tier,
            });
          }
          return;
        }

        await protocolService.connect();

        const [userState, repData] = await Promise.all([
          protocolService.getUserState(walletState.address),
          fetchReputation(walletState.address),
        ]);

        // ── Auto-claim 30 COV welcome grant for new users ──
        if (!userState.welcomeClaimed) {
          toast.loading('Welcome! Confirm in your wallet to receive 30 COV tokens…', {
            id: 'welcome-claim',
          });
          try {
            await protocolService.claimWelcome();
            // Refresh balance after claim
            const refreshed = await protocolService.getUserState(walletState.address);
            userState.covBalance = refreshed.covBalance;
            userState.welcomeClaimed = true;
            toast.success('30 COV tokens added to your account!', { id: 'welcome-claim' });
          } catch {
            toast.dismiss('welcome-claim');
            // User rejected or tx failed — they can claim manually later
          }
        }

        const isReviewer = userState.badges.some(
          (badge) => badge.type === BadgeType.REVIEWER_BADGE && badge.active
        );
        const isModerator = userState.badges.some(
          (badge) => badge.type === BadgeType.MODERATOR_BADGE && badge.active
        );

        if (!cancelled) {
          setState({
            loading: false,
            isReviewer,
            isModerator,
            covBalance: userState.covBalance,
            lockedBalance: userState.lockedBalance,
            badges: userState.badges,
            reputationScore: repData.reputation_score,
            reputationTier: repData.tier,
          });
        }
      } catch {
        if (import.meta.env.VITE_DEV_MODE === 'true') {
          const role = getAddressRole(walletState.address);
          if (!cancelled) {
            setState({
              loading: false,
              isReviewer: role === 'reviewer',
              isModerator: role === 'moderator',
              covBalance: '0', // overridden by covBalanceLive from store below
              lockedBalance: '0',
              badges: [],
              reputationScore: 0,
              reputationTier: 'tier_0',
            });
          }
          return;
        }
        if (!cancelled) setState(INITIAL);
      }
    };

    loadRoles();

    // Re-run loadRoles when MySubmissions detects a newly finalized report
    // (dispatched after moderation settlement so ProfileButton shows updated rep)
    const onRepRefresh = () => { loadRoles(); };
    window.addEventListener('covert:rep-refresh', onRepRefresh);

    // Poll every 60s so cross-browser rep/balance changes are picked up
    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') loadRoles();
    }, 60_000);

    return () => {
      cancelled = true;
      clearInterval(interval);
      window.removeEventListener('covert:rep-refresh', onRepRefresh);
    };
  }, [walletState.connected, walletState.address]);

  // In dev mode, always serve the live store balance so it updates immediately
  // after a stake without waiting for the hook's effect to re-run.
  const covBalanceOut =
    import.meta.env.VITE_DEV_MODE === 'true' && walletState.address
      ? String(covBalanceLive)
      : state.covBalance;

  return { ...state, covBalance: covBalanceOut, connected: walletState.connected };
}

export default useRoleAccess;
