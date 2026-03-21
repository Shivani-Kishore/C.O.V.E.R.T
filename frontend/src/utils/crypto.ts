/**
 * C.O.V.E.R.T - Cryptographic Utilities
 *
 * Utility functions for cryptographic operations using Web Crypto API
 */

import { HashResult, ICryptoUtils } from '../types/encryption';

/**
 * Crypto utilities implementation
 */
export const cryptoUtils: ICryptoUtils = {
  /**
   * Compute SHA-256 hash
   */
  async sha256(data: string | Uint8Array): Promise<HashResult> {
    const buffer =
      typeof data === 'string' ? new TextEncoder().encode(data) : data;

    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer as Uint8Array<ArrayBuffer>);
    const hashArray = new Uint8Array(hashBuffer) as Uint8Array<ArrayBuffer>;

    return {
      bytes: hashArray,
      hex: bytesToHex(hashArray),
      base64: bytesToBase64(hashArray),
    };
  },

  /**
   * Generate cryptographically secure random bytes
   */
  randomBytes(length: number): Uint8Array {
    return crypto.getRandomValues(new Uint8Array(length));
  },

  /**
   * Convert bytes to hexadecimal string
   */
  bytesToHex(bytes: Uint8Array): string {
    return bytesToHex(bytes);
  },

  /**
   * Convert hexadecimal string to bytes
   */
  hexToBytes(hex: string): Uint8Array {
    return hexToBytes(hex);
  },

  /**
   * Convert bytes to base64 string
   */
  bytesToBase64(bytes: Uint8Array): string {
    return bytesToBase64(bytes);
  },

  /**
   * Convert base64 string to bytes
   */
  base64ToBytes(base64: string): Uint8Array {
    return base64ToBytes(base64);
  },

  /**
   * Convert ArrayBuffer to base64 string
   */
  arrayBufferToBase64(buffer: ArrayBuffer): string {
    return bytesToBase64(new Uint8Array(buffer));
  },

  /**
   * Convert base64 string to ArrayBuffer
   */
  base64ToArrayBuffer(base64: string): ArrayBuffer {
    return base64ToBytes(base64).buffer as ArrayBuffer;
  },
};

// ===== Helper Functions =====

/**
 * Convert Uint8Array to hexadecimal string
 */
export function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Convert hexadecimal string to Uint8Array
 */
export function hexToBytes(hex: string): Uint8Array {
  // Remove 0x prefix if present
  const cleanHex = hex.startsWith('0x') ? hex.slice(2) : hex;

  if (cleanHex.length % 2 !== 0) {
    throw new Error('Invalid hex string length');
  }

  const bytes = new Uint8Array(cleanHex.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = parseInt(cleanHex.substr(i * 2, 2), 16);
  }

  return bytes;
}

/**
 * Convert Uint8Array to base64 string
 */
export function bytesToBase64(bytes: Uint8Array): string {
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Convert base64 string to Uint8Array
 */
export function base64ToBytes(base64: string): Uint8Array {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

/**
 * Convert ArrayBuffer to base64 string
 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  return bytesToBase64(new Uint8Array(buffer));
}

/**
 * Convert base64 string to ArrayBuffer
 */
export function base64ToArrayBuffer(base64: string): ArrayBuffer {
  return base64ToBytes(base64).buffer as ArrayBuffer;
}

/**
 * Compute SHA-256 hash and return as hex string
 */
export async function sha256Hex(data: string | Uint8Array): Promise<string> {
  const result = await cryptoUtils.sha256(data);
  return result.hex;
}

/**
 * Compute SHA-256 hash with 0x prefix (Ethereum format)
 */
export async function sha256Ethereum(
  data: string | Uint8Array
): Promise<string> {
  const hex = await sha256Hex(data);
  return `0x${hex}`;
}

/**
 * Generate a random UUID v4
 */
export function generateUUID(): string {
  if (crypto.randomUUID) {
    return crypto.randomUUID();
  }

  // Fallback for older browsers
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40; // Version 4
  bytes[8] = (bytes[8] & 0x3f) | 0x80; // Variant 1

  const hex = bytesToHex(bytes);
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

/**
 * Generate a cryptographically secure random string
 */
export function generateRandomString(length: number): string {
  const chars =
    'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  const bytes = crypto.getRandomValues(new Uint8Array(length));
  let result = '';
  for (let i = 0; i < length; i++) {
    result += chars[bytes[i] % chars.length];
  }
  return result;
}

/**
 * Create a fuzzy timestamp for privacy
 * Adds random offset of +/- 1-24 hours
 */
export function createFuzzyTimestamp(date: Date = new Date()): string {
  // Random offset between -24 and +24 hours
  const offsetHours = Math.random() * 48 - 24;
  const fuzzyDate = new Date(date.getTime() + offsetHours * 60 * 60 * 1000);
  return fuzzyDate.toISOString();
}

/**
 * Securely compare two strings in constant time
 * Prevents timing attacks
 */
export function constantTimeCompare(a: string, b: string): boolean {
  if (a.length !== b.length) {
    return false;
  }

  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }

  return result === 0;
}

/**
 * Securely compare two Uint8Arrays in constant time
 */
export function constantTimeCompareBytes(
  a: Uint8Array,
  b: Uint8Array
): boolean {
  if (a.length !== b.length) {
    return false;
  }

  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a[i] ^ b[i];
  }

  return result === 0;
}

/**
 * Zero out sensitive data in memory
 */
export function secureZero(arr: Uint8Array): void {
  for (let i = 0; i < arr.length; i++) {
    arr[i] = 0;
  }
}

/**
 * Combine multiple Uint8Arrays into one
 */
export function concatBytes(...arrays: Uint8Array[]): Uint8Array {
  const totalLength = arrays.reduce((sum, arr) => sum + arr.length, 0);
  const result = new Uint8Array(totalLength);

  let offset = 0;
  for (const arr of arrays) {
    result.set(arr, offset);
    offset += arr.length;
  }

  return result;
}

/**
 * Split a Uint8Array at a specific position
 */
export function splitBytes(
  arr: Uint8Array,
  position: number
): [Uint8Array, Uint8Array] {
  return [arr.slice(0, position), arr.slice(position)];
}

/**
 * Derive a deterministic key ID from key material
 * Used for tracking keys without exposing them
 */
export async function deriveKeyId(key: Uint8Array): Promise<string> {
  const hash = await cryptoUtils.sha256(key);
  return hash.hex.slice(0, 16); // First 8 bytes as hex
}

/**
 * Compute HMAC-SHA256
 */
export async function hmacSha256(
  key: Uint8Array,
  data: Uint8Array
): Promise<Uint8Array> {
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    key as Uint8Array<ArrayBuffer>,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign('HMAC', cryptoKey, data as Uint8Array<ArrayBuffer>);
  return new Uint8Array(signature);
}

/**
 * Verify HMAC-SHA256
 */
export async function verifyHmacSha256(
  key: Uint8Array,
  data: Uint8Array,
  signature: Uint8Array
): Promise<boolean> {
  const cryptoKey = await crypto.subtle.importKey(
    'raw',
    key as Uint8Array<ArrayBuffer>,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['verify']
  );

  return crypto.subtle.verify('HMAC', cryptoKey, signature as Uint8Array<ArrayBuffer>, data as Uint8Array<ArrayBuffer>);
}

/**
 * Generate a key commitment hash
 * Used to prove knowledge of key without revealing it
 */
export async function generateKeyCommitment(
  key: Uint8Array
): Promise<string> {
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const combined = concatBytes(salt, key);
  const hash = await cryptoUtils.sha256(combined);

  return `${bytesToBase64(salt)}:${hash.base64}`;
}

/**
 * Verify a key commitment
 */
export async function verifyKeyCommitment(
  key: Uint8Array,
  commitment: string
): Promise<boolean> {
  const [saltB64, hashB64] = commitment.split(':');
  if (!saltB64 || !hashB64) {
    return false;
  }

  const salt = base64ToBytes(saltB64);
  const combined = concatBytes(salt, key);
  const hash = await cryptoUtils.sha256(combined);

  return hash.base64 === hashB64;
}

export default cryptoUtils;
