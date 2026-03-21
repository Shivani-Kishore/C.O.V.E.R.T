// Central configuration — all env vars read here, nowhere else
export const API_BASE = import.meta.env.VITE_API_URL || '';
export const IS_DEV = import.meta.env.VITE_DEV_MODE === 'true';
export const CHAIN_ID = import.meta.env.VITE_CHAIN_ID || '84532';
export const RPC_URL = import.meta.env.VITE_RPC_URL || '';
export const IPFS_GATEWAY = import.meta.env.VITE_IPFS_GATEWAY || 'https://nftstorage.link/ipfs';
