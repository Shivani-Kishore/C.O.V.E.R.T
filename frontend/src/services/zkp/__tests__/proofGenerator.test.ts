import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ZKProofGenerator } from '../proofGenerator';

global.fetch = vi.fn();
global.crypto = {
  getRandomValues: (arr: Uint8Array) => {
    for (let i = 0; i < arr.length; i++) {
      arr[i] = Math.floor(Math.random() * 256);
    }
    return arr;
  },
  subtle: {
    digest: vi.fn().mockResolvedValue(new ArrayBuffer(32)),
  },
} as any;

describe('ZKProofGenerator', () => {
  let generator: ZKProofGenerator;

  beforeEach(() => {
    generator = new ZKProofGenerator();
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('initialize', () => {
    it('should fetch WASM and zkey files', async () => {
      (fetch as any).mockResolvedValue({
        ok: true,
        arrayBuffer: () => Promise.resolve(new ArrayBuffer(100)),
      });

      await generator.initialize();

      expect(fetch).toHaveBeenCalledWith('/circuits/humanity_proof_js/humanity_proof.wasm');
      expect(fetch).toHaveBeenCalledWith('/circuits/humanity_proof_final.zkey');
    });

    it('should throw error if WASM file not found', async () => {
      (fetch as any).mockResolvedValue({
        ok: false,
      });

      await expect(generator.initialize()).rejects.toThrow('Failed to load WASM file');
    });

    it('should not initialize twice', async () => {
      (fetch as any).mockResolvedValue({
        ok: true,
        arrayBuffer: () => Promise.resolve(new ArrayBuffer(100)),
      });

      await generator.initialize();
      await generator.initialize();

      expect(fetch).toHaveBeenCalledTimes(2);
    });
  });

  describe('generateSecret', () => {
    it('should generate a 32-byte hex string', () => {
      const secret = generator.generateSecret();

      expect(secret).toMatch(/^[0-9a-f]{64}$/);
    });

    it('should generate different secrets', () => {
      const secret1 = generator.generateSecret();
      const secret2 = generator.generateSecret();

      expect(secret1).not.toBe(secret2);
    });
  });

  describe('generateNullifier', () => {
    it('should generate a nullifier from secret', () => {
      const secret = '1234567890abcdef';
      const nullifier = generator.generateNullifier(secret);

      expect(nullifier).toBeTruthy();
      expect(typeof nullifier).toBe('string');
    });

    it('should generate different nullifiers for different contexts', () => {
      const secret = '1234567890abcdef';
      const nullifier1 = generator.generateNullifier(secret, 'context1');
      const nullifier2 = generator.generateNullifier(secret, 'context2');

      expect(nullifier1).not.toBe(nullifier2);
    });
  });

  describe('storeSecret', () => {
    it('should store secret in localStorage', () => {
      const secret = 'test-secret';

      generator.storeSecret(secret);

      expect(localStorage.getItem('zkp_secret')).toBe(secret);
    });
  });

  describe('loadSecret', () => {
    it('should load secret from localStorage', () => {
      const secret = 'test-secret';
      localStorage.setItem('zkp_secret', secret);

      const loaded = generator.loadSecret();

      expect(loaded).toBe(secret);
    });

    it('should return null if no secret stored', () => {
      const loaded = generator.loadSecret();

      expect(loaded).toBeNull();
    });
  });

  describe('clearSecret', () => {
    it('should remove secret from localStorage', () => {
      localStorage.setItem('zkp_secret', 'test-secret');

      generator.clearSecret();

      expect(localStorage.getItem('zkp_secret')).toBeNull();
    });
  });

  describe('hashToBigInt', () => {
    it('should convert string to BigInt representation', () => {
      const result = (generator as any).hashToBigInt('test');

      expect(typeof result).toBe('string');
      expect(Number(result)).toBeGreaterThan(0);
    });

    it('should produce consistent results', () => {
      const result1 = (generator as any).hashToBigInt('test');
      const result2 = (generator as any).hashToBigInt('test');

      expect(result1).toBe(result2);
    });
  });
});
