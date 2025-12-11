/**
 * C.O.V.E.R.T - Client-Side Encryption Service
 *
 * Implements AES-256-GCM encryption with Web Crypto API
 * All encryption happens in the browser - server never sees plaintext
 */

import {
  EncryptedPackage,
  EncryptedReportBlob,
  DecryptedReportData,
  ReportFormData,
  DecryptedAttachment,
  IEncryptionService,
  ENCRYPTION_DEFAULTS,
  EncryptionError,
} from '../types/encryption';
import {
  bytesToBase64,
  base64ToBytes,
  sha256Hex,
  createFuzzyTimestamp,
  secureZero,
} from '../utils/crypto';

/**
 * Encryption service implementation
 */
class EncryptionService implements IEncryptionService {
  private readonly keySize = ENCRYPTION_DEFAULTS.KEY_SIZE;
  private readonly ivSize = ENCRYPTION_DEFAULTS.IV_SIZE;
  private readonly blockSize = ENCRYPTION_DEFAULTS.BLOCK_SIZE;
  private readonly pbkdf2Iterations = ENCRYPTION_DEFAULTS.PBKDF2_ITERATIONS;

  /**
   * Generate a new AES-256 encryption key
   */
  async generateKey(): Promise<Uint8Array> {
    const key = crypto.getRandomValues(new Uint8Array(this.keySize / 8));
    return key;
  }

  /**
   * Encrypt data using AES-256-GCM
   */
  async encrypt(data: string, key: Uint8Array): Promise<EncryptedPackage> {
    try {
      // Generate random IV
      const iv = crypto.getRandomValues(new Uint8Array(this.ivSize));

      // Import key for encryption
      const cryptoKey = await crypto.subtle.importKey(
        'raw',
        key,
        { name: 'AES-GCM', length: this.keySize },
        false,
        ['encrypt']
      );

      // Encrypt the data
      const encodedData = new TextEncoder().encode(data);
      const ciphertext = await crypto.subtle.encrypt(
        {
          name: 'AES-GCM',
          iv: iv,
          tagLength: 128, // 16 bytes auth tag
        },
        cryptoKey,
        encodedData
      );

      // AES-GCM includes the auth tag at the end of ciphertext
      const ciphertextArray = new Uint8Array(ciphertext);

      return {
        ciphertext: bytesToBase64(ciphertextArray),
        iv: bytesToBase64(iv),
        authTag: '', // Included in ciphertext for AES-GCM
        version: ENCRYPTION_DEFAULTS.VERSION,
        algorithm: 'AES-256-GCM',
      };
    } catch (error) {
      throw this.createError('ENCRYPTION_FAILED', 'Failed to encrypt data', error);
    }
  }

  /**
   * Decrypt data using AES-256-GCM
   */
  async decrypt(encrypted: EncryptedPackage, key: Uint8Array): Promise<string> {
    try {
      // Decode base64 data
      const ciphertext = base64ToBytes(encrypted.ciphertext);
      const iv = base64ToBytes(encrypted.iv);

      // Import key for decryption
      const cryptoKey = await crypto.subtle.importKey(
        'raw',
        key,
        { name: 'AES-GCM', length: this.keySize },
        false,
        ['decrypt']
      );

      // Decrypt the data
      const plaintext = await crypto.subtle.decrypt(
        {
          name: 'AES-GCM',
          iv: iv,
          tagLength: 128,
        },
        cryptoKey,
        ciphertext
      );

      return new TextDecoder().decode(plaintext);
    } catch (error) {
      throw this.createError('DECRYPTION_FAILED', 'Failed to decrypt data', error);
    }
  }

  /**
   * Derive a key from password using PBKDF2
   */
  async deriveKey(password: string, salt: Uint8Array): Promise<Uint8Array> {
    try {
      // Import password as key material
      const keyMaterial = await crypto.subtle.importKey(
        'raw',
        new TextEncoder().encode(password),
        'PBKDF2',
        false,
        ['deriveBits']
      );

      // Derive key using PBKDF2
      const derivedBits = await crypto.subtle.deriveBits(
        {
          name: 'PBKDF2',
          salt: salt,
          iterations: this.pbkdf2Iterations,
          hash: 'SHA-256',
        },
        keyMaterial,
        this.keySize
      );

      return new Uint8Array(derivedBits);
    } catch (error) {
      throw this.createError('KEY_DERIVATION_FAILED', 'Failed to derive key', error);
    }
  }

  /**
   * Pad data to fixed block size for size obfuscation
   */
  padData(data: string, blockSize: number = this.blockSize): string {
    const dataBytes = new TextEncoder().encode(data);
    const dataLength = dataBytes.length;

    // Calculate number of blocks needed
    const blocksNeeded = Math.ceil(dataLength / blockSize);
    const paddedLength = blocksNeeded * blockSize;

    // Create padding
    const paddingLength = paddedLength - dataLength;
    const padding = crypto.getRandomValues(new Uint8Array(paddingLength));

    // Combine data and padding
    const paddedData = new Uint8Array(paddedLength + 4); // +4 for original length
    const lengthBytes = new Uint8Array(4);
    new DataView(lengthBytes.buffer).setUint32(0, dataLength, false);

    paddedData.set(lengthBytes, 0);
    paddedData.set(dataBytes, 4);
    paddedData.set(padding, 4 + dataLength);

    return bytesToBase64(paddedData);
  }

  /**
   * Remove padding from data
   */
  unpadData(paddedData: string): string {
    const bytes = base64ToBytes(paddedData);

    // Extract original length from first 4 bytes
    const lengthBytes = bytes.slice(0, 4);
    const originalLength = new DataView(lengthBytes.buffer).getUint32(0, false);

    // Extract original data
    const data = bytes.slice(4, 4 + originalLength);

    return new TextDecoder().decode(data);
  }

  /**
   * Encrypt a complete report with all attachments
   */
  async encryptReport(
    formData: ReportFormData
  ): Promise<{ blob: EncryptedReportBlob; key: Uint8Array }> {
    // Generate encryption key
    const key = await this.generateKey();

    // Process file attachments
    const attachments: DecryptedAttachment[] = await Promise.all(
      formData.files.map(async (file) => ({
        filename: file.name,
        mimeType: file.type,
        size: file.size,
        content: await this.fileToBase64(file),
      }))
    );

    // Create report data structure
    const reportData: DecryptedReportData = {
      title: formData.title,
      category: formData.category,
      description: formData.description,
      timestamp: createFuzzyTimestamp(),
      attachments,
    };

    // Serialize and pad the data
    const serialized = JSON.stringify(reportData);
    const paddedData = this.padData(serialized);

    // Encrypt the padded data
    const encryptedPayload = await this.encrypt(paddedData, key);

    // Create the encrypted blob
    const blob: EncryptedReportBlob = {
      version: ENCRYPTION_DEFAULTS.VERSION,
      encrypted_payload: encryptedPayload,
      metadata: {
        originalSize: new TextEncoder().encode(serialized).length,
        paddedSize: base64ToBytes(paddedData).length,
        timestamp: createFuzzyTimestamp(),
        fileCount: formData.files.length,
      },
    };

    return { blob, key };
  }

  /**
   * Decrypt a complete report
   */
  async decryptReport(
    blob: EncryptedReportBlob,
    key: Uint8Array
  ): Promise<DecryptedReportData> {
    // Decrypt the payload
    const paddedData = await this.decrypt(blob.encrypted_payload, key);

    // Remove padding
    const serialized = this.unpadData(paddedData);

    // Parse the report data
    const reportData: DecryptedReportData = JSON.parse(serialized);

    return reportData;
  }

  /**
   * Encrypt a key with a wallet-derived key
   */
  async encryptKeyWithWallet(
    reportKey: Uint8Array,
    walletKey: Uint8Array
  ): Promise<string> {
    const encrypted = await this.encrypt(
      bytesToBase64(reportKey),
      walletKey
    );
    return JSON.stringify(encrypted);
  }

  /**
   * Decrypt a key with a wallet-derived key
   */
  async decryptKeyWithWallet(
    encryptedKey: string,
    walletKey: Uint8Array
  ): Promise<Uint8Array> {
    const encrypted: EncryptedPackage = JSON.parse(encryptedKey);
    const keyBase64 = await this.decrypt(encrypted, walletKey);
    return base64ToBytes(keyBase64);
  }

  /**
   * Store encryption key in local storage (encrypted)
   */
  async storeKey(
    cid: string,
    reportKey: Uint8Array,
    walletAddress: string,
    walletSignature: string
  ): Promise<void> {
    // Derive storage key from wallet signature
    const salt = new TextEncoder().encode(`covert-key-${cid}`);
    const storageKey = await this.deriveKey(walletSignature, salt);

    // Encrypt the report key
    const encryptedKey = await this.encryptKeyWithWallet(reportKey, storageKey);

    // Compute key hash for verification
    const keyHash = await sha256Hex(reportKey);

    // Store in local storage
    const entry = {
      cid,
      encryptedKey,
      keyHash,
      walletAddress,
      storedAt: new Date().toISOString(),
    };

    localStorage.setItem(`covert_key_${cid}`, JSON.stringify(entry));

    // Clear sensitive data from memory
    secureZero(storageKey);
  }

  /**
   * Retrieve encryption key from local storage
   */
  async retrieveKey(
    cid: string,
    walletSignature: string
  ): Promise<Uint8Array> {
    const storedEntry = localStorage.getItem(`covert_key_${cid}`);
    if (!storedEntry) {
      throw this.createError('DECRYPTION_FAILED', `Key not found for CID: ${cid}`);
    }

    const entry = JSON.parse(storedEntry);

    // Derive storage key from wallet signature
    const salt = new TextEncoder().encode(`covert-key-${cid}`);
    const storageKey = await this.deriveKey(walletSignature, salt);

    // Decrypt the report key
    const reportKey = await this.decryptKeyWithWallet(entry.encryptedKey, storageKey);

    // Verify key hash
    const computedHash = await sha256Hex(reportKey);
    if (computedHash !== entry.keyHash) {
      throw this.createError('DECRYPTION_FAILED', 'Key verification failed');
    }

    // Clear sensitive data from memory
    secureZero(storageKey);

    return reportKey;
  }

  /**
   * List all stored keys
   */
  listStoredKeys(): string[] {
    const keys: string[] = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key?.startsWith('covert_key_')) {
        keys.push(key.replace('covert_key_', ''));
      }
    }
    return keys;
  }

  /**
   * Delete a stored key
   */
  deleteStoredKey(cid: string): void {
    localStorage.removeItem(`covert_key_${cid}`);
  }

  /**
   * Hash a CID using SHA-256 (for blockchain commitment)
   */
  async hashCID(cid: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(cid);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = new Uint8Array(hashBuffer);
    const hashHex = Array.from(hashArray)
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
    return '0x' + hashHex;
  }

  /**
   * Convert File to base64 string
   */
  private async fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result as string;
        // Remove data URL prefix
        const base64 = result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(file);
    });
  }

  /**
   * Create a typed encryption error
   */
  private createError(
    code: EncryptionError['code'],
    message: string,
    cause?: unknown
  ): EncryptionError {
    return {
      code,
      message,
      cause: cause instanceof Error ? cause : undefined,
    };
  }
}

// Export singleton instance
export const encryptionService = new EncryptionService();

// Export class for testing
export { EncryptionService };

export default encryptionService;
