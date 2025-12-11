/**
 * C.O.V.E.R.T - Encryption Service Tests
 *
 * Comprehensive tests for client-side encryption functionality
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { EncryptionService } from '../services/encryption';
import { cryptoUtils, bytesToBase64, base64ToBytes } from '../utils/crypto';
import {
  EncryptedPackage,
  ReportFormData,
  ENCRYPTION_DEFAULTS,
} from '../types/encryption';

describe('EncryptionService', () => {
  let encryptionService: EncryptionService;

  beforeEach(() => {
    encryptionService = new EncryptionService();
  });

  describe('generateKey', () => {
    it('should generate a 256-bit key', async () => {
      const key = await encryptionService.generateKey();
      expect(key).toBeInstanceOf(Uint8Array);
      expect(key.length).toBe(32); // 256 bits = 32 bytes
    });

    it('should generate unique keys each time', async () => {
      const key1 = await encryptionService.generateKey();
      const key2 = await encryptionService.generateKey();
      expect(bytesToBase64(key1)).not.toBe(bytesToBase64(key2));
    });
  });

  describe('encrypt/decrypt', () => {
    it('should encrypt and decrypt text correctly', async () => {
      const key = await encryptionService.generateKey();
      const plaintext = 'Hello, C.O.V.E.R.T!';

      const encrypted = await encryptionService.encrypt(plaintext, key);
      const decrypted = await encryptionService.decrypt(encrypted, key);

      expect(decrypted).toBe(plaintext);
    });

    it('should encrypt and decrypt JSON data', async () => {
      const key = await encryptionService.generateKey();
      const data = {
        title: 'Test Report',
        description: 'This is a test report with sensitive information',
        category: 'corruption',
      };
      const plaintext = JSON.stringify(data);

      const encrypted = await encryptionService.encrypt(plaintext, key);
      const decrypted = await encryptionService.decrypt(encrypted, key);

      expect(JSON.parse(decrypted)).toEqual(data);
    });

    it('should encrypt and decrypt large data', async () => {
      const key = await encryptionService.generateKey();
      const plaintext = 'A'.repeat(100000); // 100KB of data

      const encrypted = await encryptionService.encrypt(plaintext, key);
      const decrypted = await encryptionService.decrypt(encrypted, key);

      expect(decrypted).toBe(plaintext);
    });

    it('should produce different ciphertext for same plaintext', async () => {
      const key = await encryptionService.generateKey();
      const plaintext = 'Same message';

      const encrypted1 = await encryptionService.encrypt(plaintext, key);
      const encrypted2 = await encryptionService.encrypt(plaintext, key);

      // Different IVs should produce different ciphertext
      expect(encrypted1.ciphertext).not.toBe(encrypted2.ciphertext);
      expect(encrypted1.iv).not.toBe(encrypted2.iv);
    });

    it('should fail to decrypt with wrong key', async () => {
      const key1 = await encryptionService.generateKey();
      const key2 = await encryptionService.generateKey();
      const plaintext = 'Secret message';

      const encrypted = await encryptionService.encrypt(plaintext, key1);

      await expect(
        encryptionService.decrypt(encrypted, key2)
      ).rejects.toMatchObject({
        code: 'DECRYPTION_FAILED',
      });
    });

    it('should fail to decrypt tampered ciphertext', async () => {
      const key = await encryptionService.generateKey();
      const plaintext = 'Secret message';

      const encrypted = await encryptionService.encrypt(plaintext, key);

      // Tamper with ciphertext
      const tamperedBytes = base64ToBytes(encrypted.ciphertext);
      tamperedBytes[0] ^= 0xff; // Flip bits
      encrypted.ciphertext = bytesToBase64(tamperedBytes);

      await expect(
        encryptionService.decrypt(encrypted, key)
      ).rejects.toMatchObject({
        code: 'DECRYPTION_FAILED',
      });
    });

    it('should include correct metadata in encrypted package', async () => {
      const key = await encryptionService.generateKey();
      const plaintext = 'Test message';

      const encrypted = await encryptionService.encrypt(plaintext, key);

      expect(encrypted.version).toBe(ENCRYPTION_DEFAULTS.VERSION);
      expect(encrypted.algorithm).toBe('AES-256-GCM');
      expect(encrypted.iv).toBeTruthy();
      expect(encrypted.ciphertext).toBeTruthy();
    });
  });

  describe('deriveKey', () => {
    it('should derive consistent key from password and salt', async () => {
      const password = 'TestPassword123!';
      const salt = crypto.getRandomValues(new Uint8Array(16));

      const key1 = await encryptionService.deriveKey(password, salt);
      const key2 = await encryptionService.deriveKey(password, salt);

      expect(bytesToBase64(key1)).toBe(bytesToBase64(key2));
    });

    it('should derive different keys for different passwords', async () => {
      const salt = crypto.getRandomValues(new Uint8Array(16));

      const key1 = await encryptionService.deriveKey('password1', salt);
      const key2 = await encryptionService.deriveKey('password2', salt);

      expect(bytesToBase64(key1)).not.toBe(bytesToBase64(key2));
    });

    it('should derive different keys for different salts', async () => {
      const password = 'same-password';
      const salt1 = crypto.getRandomValues(new Uint8Array(16));
      const salt2 = crypto.getRandomValues(new Uint8Array(16));

      const key1 = await encryptionService.deriveKey(password, salt1);
      const key2 = await encryptionService.deriveKey(password, salt2);

      expect(bytesToBase64(key1)).not.toBe(bytesToBase64(key2));
    });

    it('should produce a 256-bit key', async () => {
      const password = 'TestPassword';
      const salt = crypto.getRandomValues(new Uint8Array(16));

      const key = await encryptionService.deriveKey(password, salt);

      expect(key.length).toBe(32); // 256 bits
    });
  });

  describe('padData/unpadData', () => {
    it('should pad data to block size', () => {
      const data = 'Short message';
      const blockSize = 65536; // 64KB

      const padded = encryptionService.padData(data, blockSize);
      const paddedBytes = base64ToBytes(padded);

      expect(paddedBytes.length).toBe(blockSize);
    });

    it('should preserve original data after unpadding', () => {
      const data = 'Original message with special chars: !@#$%^&*()';

      const padded = encryptionService.padData(data);
      const unpadded = encryptionService.unpadData(padded);

      expect(unpadded).toBe(data);
    });

    it('should handle empty data', () => {
      const data = '';

      const padded = encryptionService.padData(data);
      const unpadded = encryptionService.unpadData(padded);

      expect(unpadded).toBe(data);
    });

    it('should handle large data that spans multiple blocks', () => {
      const data = 'X'.repeat(200000); // ~200KB
      const blockSize = 65536;

      const padded = encryptionService.padData(data, blockSize);
      const paddedBytes = base64ToBytes(padded);

      // Should be padded to next block boundary
      expect(paddedBytes.length % blockSize).toBe(0);
      expect(paddedBytes.length).toBeGreaterThanOrEqual(data.length);

      const unpadded = encryptionService.unpadData(padded);
      expect(unpadded).toBe(data);
    });

    it('should handle unicode data', () => {
      const data = 'Unicode: 你好世界 🌍 Ω∑∏';

      const padded = encryptionService.padData(data);
      const unpadded = encryptionService.unpadData(padded);

      expect(unpadded).toBe(data);
    });
  });

  describe('encryptReport/decryptReport', () => {
    it('should encrypt and decrypt a complete report', async () => {
      // Create a mock file
      const fileContent = new Blob(['test file content'], { type: 'text/plain' });
      const mockFile = new File([fileContent], 'test.txt', { type: 'text/plain' });

      const formData: ReportFormData = {
        title: 'Test Report',
        category: 'corruption',
        description: 'This is a test report',
        files: [mockFile],
        visibility: 'moderated',
      };

      const { blob, key } = await encryptionService.encryptReport(formData);
      const decrypted = await encryptionService.decryptReport(blob, key);

      expect(decrypted.title).toBe(formData.title);
      expect(decrypted.category).toBe(formData.category);
      expect(decrypted.description).toBe(formData.description);
      expect(decrypted.attachments).toHaveLength(1);
      expect(decrypted.attachments[0].filename).toBe('test.txt');
    });

    it('should include metadata in encrypted blob', async () => {
      const formData: ReportFormData = {
        title: 'Test',
        category: 'fraud',
        description: 'Test description',
        files: [],
        visibility: 'private',
      };

      const { blob } = await encryptionService.encryptReport(formData);

      expect(blob.version).toBe(ENCRYPTION_DEFAULTS.VERSION);
      expect(blob.metadata.fileCount).toBe(0);
      expect(blob.metadata.originalSize).toBeGreaterThan(0);
      expect(blob.metadata.paddedSize).toBeGreaterThan(0);
    });

    it('should create fuzzy timestamp', async () => {
      const formData: ReportFormData = {
        title: 'Test',
        category: 'safety',
        description: 'Test',
        files: [],
        visibility: 'public',
      };

      const { blob } = await encryptionService.encryptReport(formData);

      // Timestamp should be ISO format
      expect(blob.metadata.timestamp).toMatch(
        /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/
      );
    });
  });

  describe('key storage', () => {
    beforeEach(() => {
      // Clear localStorage before each test
      localStorage.clear();
    });

    it('should store and retrieve encryption key', async () => {
      const cid = 'QmTestCID123456789';
      const key = await encryptionService.generateKey();
      const walletAddress = '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb';
      const signature = 'test-signature-data';

      await encryptionService.storeKey(cid, key, walletAddress, signature);
      const retrievedKey = await encryptionService.retrieveKey(cid, signature);

      expect(bytesToBase64(retrievedKey)).toBe(bytesToBase64(key));
    });

    it('should list stored keys', async () => {
      const key = await encryptionService.generateKey();
      const signature = 'test-signature';

      await encryptionService.storeKey('cid1', key, '0x123', signature);
      await encryptionService.storeKey('cid2', key, '0x123', signature);

      const storedKeys = encryptionService.listStoredKeys();

      expect(storedKeys).toContain('cid1');
      expect(storedKeys).toContain('cid2');
    });

    it('should delete stored key', async () => {
      const cid = 'QmTestDelete';
      const key = await encryptionService.generateKey();

      await encryptionService.storeKey(cid, key, '0x123', 'sig');

      let storedKeys = encryptionService.listStoredKeys();
      expect(storedKeys).toContain(cid);

      encryptionService.deleteStoredKey(cid);

      storedKeys = encryptionService.listStoredKeys();
      expect(storedKeys).not.toContain(cid);
    });

    it('should throw error for non-existent key', async () => {
      await expect(
        encryptionService.retrieveKey('nonexistent', 'sig')
      ).rejects.toMatchObject({
        code: 'DECRYPTION_FAILED',
      });
    });
  });
});

describe('cryptoUtils', () => {
  describe('sha256', () => {
    it('should compute correct SHA-256 hash', async () => {
      const data = 'test data';
      const result = await cryptoUtils.sha256(data);

      // Known SHA-256 hash of "test data"
      expect(result.hex).toBe(
        '916f0027a575074ce72a331777c3478d6513f786a591bd892da1a577bf2335f9'
      );
    });

    it('should produce consistent hashes', async () => {
      const data = 'consistent data';

      const hash1 = await cryptoUtils.sha256(data);
      const hash2 = await cryptoUtils.sha256(data);

      expect(hash1.hex).toBe(hash2.hex);
    });

    it('should work with Uint8Array input', async () => {
      const data = new TextEncoder().encode('byte data');
      const result = await cryptoUtils.sha256(data);

      expect(result.hex).toHaveLength(64);
      expect(result.bytes).toHaveLength(32);
    });
  });

  describe('randomBytes', () => {
    it('should generate correct length', () => {
      const bytes = cryptoUtils.randomBytes(32);
      expect(bytes.length).toBe(32);
    });

    it('should generate different values each time', () => {
      const bytes1 = cryptoUtils.randomBytes(16);
      const bytes2 = cryptoUtils.randomBytes(16);

      expect(bytesToBase64(bytes1)).not.toBe(bytesToBase64(bytes2));
    });
  });

  describe('encoding conversions', () => {
    it('should convert bytes to hex and back', () => {
      const original = crypto.getRandomValues(new Uint8Array(32));
      const hex = cryptoUtils.bytesToHex(original);
      const converted = cryptoUtils.hexToBytes(hex);

      expect(bytesToBase64(converted)).toBe(bytesToBase64(original));
    });

    it('should convert bytes to base64 and back', () => {
      const original = crypto.getRandomValues(new Uint8Array(32));
      const base64 = cryptoUtils.bytesToBase64(original);
      const converted = cryptoUtils.base64ToBytes(base64);

      expect(bytesToBase64(converted)).toBe(bytesToBase64(original));
    });

    it('should handle 0x prefix in hex', () => {
      const hex = '0x1234567890abcdef';
      const bytes = cryptoUtils.hexToBytes(hex);
      const backToHex = cryptoUtils.bytesToHex(bytes);

      expect(backToHex).toBe('1234567890abcdef');
    });
  });
});
