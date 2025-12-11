/**
 * C.O.V.E.R.T - Encryption Type Definitions
 *
 * TypeScript types for encryption, IPFS, and cryptographic operations
 */

// ===== Encryption Types =====

/**
 * AES-GCM encrypted data package
 */
export interface EncryptedPackage {
  /** Base64 encoded ciphertext */
  ciphertext: string;
  /** Base64 encoded initialization vector (12 bytes) */
  iv: string;
  /** Base64 encoded authentication tag (16 bytes) */
  authTag: string;
  /** Encryption algorithm version */
  version: number;
  /** Algorithm used */
  algorithm: 'AES-256-GCM';
}

/**
 * Complete encrypted report blob for IPFS storage
 */
export interface EncryptedReportBlob {
  /** Version of the encryption format */
  version: number;
  /** Encrypted payload */
  encrypted_payload: EncryptedPackage;
  /** Metadata about the encrypted content */
  metadata: {
    /** Original size before padding */
    originalSize: number;
    /** Padded size */
    paddedSize: number;
    /** Timestamp (fuzzy for privacy) */
    timestamp: string;
    /** File count */
    fileCount: number;
  };
}

/**
 * Decrypted report data structure
 */
export interface DecryptedReportData {
  /** Report title */
  title: string;
  /** Report category */
  category: ReportCategory;
  /** Report description */
  description: string;
  /** Fuzzy timestamp */
  timestamp: string;
  /** Attached files */
  attachments: DecryptedAttachment[];
}

/**
 * Decrypted file attachment
 */
export interface DecryptedAttachment {
  /** File name */
  filename: string;
  /** MIME type */
  mimeType: string;
  /** File size in bytes */
  size: number;
  /** Base64 encoded file content */
  content: string;
}

/**
 * Report categories
 */
export type ReportCategory =
  | 'corruption'
  | 'harassment'
  | 'fraud'
  | 'safety'
  | 'environmental'
  | 'discrimination'
  | 'other';

/**
 * Report visibility options
 */
export type ReportVisibility = 'private' | 'moderated' | 'public';

// ===== Key Management Types =====

/**
 * Encryption key with metadata
 */
export interface EncryptionKey {
  /** Raw key bytes */
  key: Uint8Array;
  /** Key identifier (derived from content) */
  keyId: string;
  /** When the key was generated */
  createdAt: Date;
}

/**
 * Stored key entry (encrypted with wallet)
 */
export interface StoredKeyEntry {
  /** IPFS CID this key is for */
  cid: string;
  /** Base64 encoded encrypted key */
  encryptedKey: string;
  /** Hash of the encryption key for verification */
  keyHash: string;
  /** When the key was stored */
  storedAt: string;
}

/**
 * Key derivation parameters
 */
export interface KeyDerivationParams {
  /** PBKDF2 salt */
  salt: Uint8Array;
  /** Number of iterations */
  iterations: number;
  /** Hash algorithm */
  hash: 'SHA-256' | 'SHA-512';
  /** Derived key length in bits */
  keyLength: 256 | 512;
}

// ===== IPFS Types =====

/**
 * IPFS upload result
 */
export interface IPFSUploadResult {
  /** Content Identifier */
  cid: string;
  /** Full IPFS gateway URL */
  gatewayUrl: string;
  /** Size of uploaded content */
  size: number;
}

/**
 * IPFS upload progress
 */
export interface IPFSUploadProgress {
  /** Bytes uploaded so far */
  loaded: number;
  /** Total bytes to upload */
  total: number;
  /** Progress percentage (0-100) */
  percentage: number;
}

/**
 * IPFS pin status
 */
export interface IPFSPinStatus {
  /** CID being checked */
  cid: string;
  /** Whether it's pinned */
  isPinned: boolean;
  /** Pin provider */
  provider: 'local' | 'pinata' | 'web3storage';
  /** When it was pinned */
  pinnedAt?: string;
}

// ===== Report Submission Types =====

/**
 * Report form data before encryption
 */
export interface ReportFormData {
  /** Report title */
  title: string;
  /** Report category */
  category: ReportCategory;
  /** Report description */
  description: string;
  /** File attachments */
  files: File[];
  /** Visibility setting */
  visibility: ReportVisibility;
}

/**
 * Prepared report for submission
 */
export interface PreparedReport {
  /** Encrypted blob for IPFS */
  encryptedBlob: EncryptedReportBlob;
  /** Encryption key (for local storage) */
  encryptionKey: Uint8Array;
  /** SHA-256 hash of CID (for blockchain) */
  cidHash: string;
  /** Size of encrypted data */
  encryptedSize: number;
}

/**
 * Report submission result
 */
export interface ReportSubmissionResult {
  /** Report ID from backend */
  reportId: string;
  /** IPFS CID */
  ipfsCid: string;
  /** Blockchain transaction hash */
  transactionHash: string;
  /** Block number */
  blockNumber: number;
  /** Submission timestamp */
  timestamp: string;
  /** Report status */
  status: ReportStatus;
}

/**
 * Report status values
 */
export type ReportStatus =
  | 'pending'
  | 'under_review'
  | 'verified'
  | 'rejected'
  | 'disputed'
  | 'archived';

// ===== Crypto Utility Types =====

/**
 * Hash result
 */
export interface HashResult {
  /** Hex encoded hash */
  hex: string;
  /** Base64 encoded hash */
  base64: string;
  /** Raw bytes */
  bytes: Uint8Array;
}

/**
 * Random data generation options
 */
export interface RandomOptions {
  /** Number of bytes to generate */
  length: number;
  /** Output format */
  format: 'bytes' | 'hex' | 'base64';
}

// ===== Error Types =====

/**
 * Encryption error
 */
export interface EncryptionError {
  /** Error code */
  code: 'ENCRYPTION_FAILED' | 'DECRYPTION_FAILED' | 'KEY_DERIVATION_FAILED' | 'INVALID_DATA';
  /** Error message */
  message: string;
  /** Original error */
  cause?: Error;
}

/**
 * IPFS error
 */
export interface IPFSError {
  /** Error code */
  code: 'UPLOAD_FAILED' | 'PIN_FAILED' | 'RETRIEVAL_FAILED' | 'GATEWAY_ERROR';
  /** Error message */
  message: string;
  /** Retry count */
  retryCount?: number;
  /** Original error */
  cause?: Error;
}

// ===== Wallet Integration Types =====

/**
 * Wallet signature result
 */
export interface WalletSignature {
  /** Signature bytes */
  signature: string;
  /** Message that was signed */
  message: string;
  /** Wallet address */
  address: string;
}

/**
 * Burner wallet
 */
export interface BurnerWallet {
  /** Wallet address */
  address: string;
  /** Private key (never expose) */
  privateKey: string;
  /** Mnemonic phrase (for recovery) */
  mnemonic?: string;
}

// ===== Service Interfaces =====

/**
 * Encryption service interface
 */
export interface IEncryptionService {
  generateKey(): Promise<Uint8Array>;
  encrypt(data: string, key: Uint8Array): Promise<EncryptedPackage>;
  decrypt(encrypted: EncryptedPackage, key: Uint8Array): Promise<string>;
  deriveKey(password: string, salt: Uint8Array): Promise<Uint8Array>;
  padData(data: string, blockSize: number): string;
  unpadData(paddedData: string): string;
}

/**
 * IPFS service interface
 */
export interface IIPFSService {
  upload(
    data: EncryptedReportBlob,
    onProgress?: (progress: IPFSUploadProgress) => void
  ): Promise<IPFSUploadResult>;
  retrieve(cid: string): Promise<EncryptedReportBlob>;
  pin(cid: string): Promise<IPFSPinStatus>;
  unpin(cid: string): Promise<void>;
  getGatewayUrl(cid: string): string;
}

/**
 * Crypto utilities interface
 */
export interface ICryptoUtils {
  sha256(data: string | Uint8Array): Promise<HashResult>;
  randomBytes(length: number): Uint8Array;
  bytesToHex(bytes: Uint8Array): string;
  hexToBytes(hex: string): Uint8Array;
  bytesToBase64(bytes: Uint8Array): string;
  base64ToBytes(base64: string): Uint8Array;
  arrayBufferToBase64(buffer: ArrayBuffer): string;
  base64ToArrayBuffer(base64: string): ArrayBuffer;
}

// ===== Constants =====

/**
 * Default encryption parameters
 */
export const ENCRYPTION_DEFAULTS = {
  /** AES key size in bits */
  KEY_SIZE: 256,
  /** IV size in bytes */
  IV_SIZE: 12,
  /** Auth tag size in bytes */
  AUTH_TAG_SIZE: 16,
  /** Block size for padding */
  BLOCK_SIZE: 65536, // 64KB
  /** PBKDF2 iterations */
  PBKDF2_ITERATIONS: 100000,
  /** Current encryption version */
  VERSION: 1,
} as const;

/**
 * IPFS configuration
 */
export const IPFS_CONFIG = {
  /** Default gateway URL */
  GATEWAY_URL: 'https://nftstorage.link/ipfs',
  /** Maximum file size (100MB) */
  MAX_FILE_SIZE: 100 * 1024 * 1024,
  /** Upload timeout (5 minutes) */
  UPLOAD_TIMEOUT: 300000,
  /** Max retry attempts */
  MAX_RETRIES: 3,
  /** Retry delay (1 second) */
  RETRY_DELAY: 1000,
} as const;
