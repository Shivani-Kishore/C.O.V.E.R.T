/**
 * C.O.V.E.R.T - IPFS Storage Service
 *
 * Handles encrypted blob storage on IPFS with NFT.Storage/web3.storage
 */

import {
  EncryptedReportBlob,
  IPFSUploadResult,
  IPFSUploadProgress,
  IPFSPinStatus,
  IIPFSService,
  IPFS_CONFIG,
  IPFSError,
} from '../types/encryption';

/**
 * IPFS service implementation
 */
class IPFSService implements IIPFSService {
  private nftStorageToken: string = '';
  private web3StorageToken: string = '';
  private localGateway: string = IPFS_CONFIG.GATEWAY_URL;

  /**
   * Configure the IPFS service
   */
  configure(config: {
    nftStorageToken?: string;
    web3StorageToken?: string;
    localGateway?: string;
  }): void {
    if (config.nftStorageToken) {
      this.nftStorageToken = config.nftStorageToken;
    }
    if (config.web3StorageToken) {
      this.web3StorageToken = config.web3StorageToken;
    }
    if (config.localGateway) {
      this.localGateway = config.localGateway;
    }
  }

  /**
   * Upload encrypted blob to IPFS
   */
  async upload(
    data: EncryptedReportBlob,
    onProgress?: (progress: IPFSUploadProgress) => void
  ): Promise<IPFSUploadResult> {
    // Serialize the data
    const jsonData = JSON.stringify(data);
    const blob = new Blob([jsonData], { type: 'application/json' });

    // Check file size
    if (blob.size > IPFS_CONFIG.MAX_FILE_SIZE) {
      throw this.createError(
        'UPLOAD_FAILED',
        `File size ${blob.size} exceeds maximum ${IPFS_CONFIG.MAX_FILE_SIZE}`
      );
    }

    // Try NFT.Storage first, then web3.storage, then local
    let lastError: Error | undefined;

    // Try NFT.Storage
    if (this.nftStorageToken) {
      try {
        return await this.uploadToNFTStorage(blob, onProgress);
      } catch (error) {
        console.warn('NFT.Storage upload failed, trying fallback:', error);
        lastError = error instanceof Error ? error : new Error(String(error));
      }
    }

    // Try web3.storage
    if (this.web3StorageToken) {
      try {
        return await this.uploadToWeb3Storage(blob, onProgress);
      } catch (error) {
        console.warn('web3.storage upload failed, trying fallback:', error);
        lastError = error instanceof Error ? error : new Error(String(error));
      }
    }

    // Try local IPFS node
    try {
      return await this.uploadToLocalIPFS(blob, onProgress);
    } catch (error) {
      console.warn('Local IPFS upload failed:', error);
      lastError = error instanceof Error ? error : new Error(String(error));
    }

    throw this.createError(
      'UPLOAD_FAILED',
      'All IPFS upload methods failed',
      lastError
    );
  }

  /**
   * Upload to NFT.Storage
   */
  private async uploadToNFTStorage(
    blob: Blob,
    onProgress?: (progress: IPFSUploadProgress) => void
  ): Promise<IPFSUploadResult> {
    const totalSize = blob.size;

    // Simulate progress for fetch (no real progress API)
    if (onProgress) {
      onProgress({ loaded: 0, total: totalSize, percentage: 0 });
    }

    const response = await this.fetchWithRetry(
      'https://api.nft.storage/upload',
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.nftStorageToken}`,
        },
        body: blob,
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`NFT.Storage error: ${response.status} - ${errorText}`);
    }

    const result = await response.json();

    if (onProgress) {
      onProgress({ loaded: totalSize, total: totalSize, percentage: 100 });
    }

    return {
      cid: result.value.cid,
      gatewayUrl: `https://nftstorage.link/ipfs/${result.value.cid}`,
      size: totalSize,
    };
  }

  /**
   * Upload to web3.storage
   */
  private async uploadToWeb3Storage(
    blob: Blob,
    onProgress?: (progress: IPFSUploadProgress) => void
  ): Promise<IPFSUploadResult> {
    const totalSize = blob.size;

    if (onProgress) {
      onProgress({ loaded: 0, total: totalSize, percentage: 0 });
    }

    const response = await this.fetchWithRetry(
      'https://api.web3.storage/upload',
      {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${this.web3StorageToken}`,
          'X-Name': `report_${Date.now()}`,
        },
        body: blob,
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`web3.storage error: ${response.status} - ${errorText}`);
    }

    const result = await response.json();

    if (onProgress) {
      onProgress({ loaded: totalSize, total: totalSize, percentage: 100 });
    }

    return {
      cid: result.cid,
      gatewayUrl: `https://w3s.link/ipfs/${result.cid}`,
      size: totalSize,
    };
  }

  /**
   * Upload to local IPFS node
   */
  private async uploadToLocalIPFS(
    blob: Blob,
    onProgress?: (progress: IPFSUploadProgress) => void
  ): Promise<IPFSUploadResult> {
    const totalSize = blob.size;

    if (onProgress) {
      onProgress({ loaded: 0, total: totalSize, percentage: 0 });
    }

    const formData = new FormData();
    formData.append('file', blob);

    const response = await this.fetchWithRetry(
      'http://localhost:5001/api/v0/add',
      {
        method: 'POST',
        body: formData,
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Local IPFS error: ${response.status} - ${errorText}`);
    }

    const result = await response.json();

    if (onProgress) {
      onProgress({ loaded: totalSize, total: totalSize, percentage: 100 });
    }

    return {
      cid: result.Hash,
      gatewayUrl: `http://localhost:8080/ipfs/${result.Hash}`,
      size: totalSize,
    };
  }

  /**
   * Retrieve encrypted blob from IPFS
   */
  async retrieve(cid: string): Promise<EncryptedReportBlob> {
    // Try multiple gateways
    const gateways = [
      `https://nftstorage.link/ipfs/${cid}`,
      `https://w3s.link/ipfs/${cid}`,
      `https://ipfs.io/ipfs/${cid}`,
      `https://cloudflare-ipfs.com/ipfs/${cid}`,
      `http://localhost:8080/ipfs/${cid}`,
    ];

    let lastError: Error | undefined;

    for (const gatewayUrl of gateways) {
      try {
        const response = await this.fetchWithRetry(gatewayUrl, {
          method: 'GET',
          headers: {
            Accept: 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Gateway returned ${response.status}`);
        }

        const data: EncryptedReportBlob = await response.json();
        return data;
      } catch (error) {
        console.warn(`Failed to retrieve from ${gatewayUrl}:`, error);
        lastError = error instanceof Error ? error : new Error(String(error));
        continue;
      }
    }

    throw this.createError(
      'RETRIEVAL_FAILED',
      `Failed to retrieve CID ${cid} from all gateways`,
      lastError
    );
  }

  /**
   * Pin CID to ensure persistence
   */
  async pin(cid: string): Promise<IPFSPinStatus> {
    // Try NFT.Storage
    if (this.nftStorageToken) {
      try {
        const response = await this.fetchWithRetry(
          `https://api.nft.storage/pins/${cid}`,
          {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${this.nftStorageToken}`,
            },
          }
        );

        if (response.ok) {
          return {
            cid,
            isPinned: true,
            provider: 'pinata',
            pinnedAt: new Date().toISOString(),
          };
        }
      } catch (error) {
        console.warn('NFT.Storage pin failed:', error);
      }
    }

    // Try local IPFS
    try {
      const response = await this.fetchWithRetry(
        `http://localhost:5001/api/v0/pin/add?arg=${cid}`,
        {
          method: 'POST',
        }
      );

      if (response.ok) {
        return {
          cid,
          isPinned: true,
          provider: 'local',
          pinnedAt: new Date().toISOString(),
        };
      }
    } catch (error) {
      console.warn('Local IPFS pin failed:', error);
    }

    throw this.createError('PIN_FAILED', `Failed to pin CID ${cid}`);
  }

  /**
   * Unpin CID
   */
  async unpin(cid: string): Promise<void> {
    // Try local IPFS
    try {
      const response = await fetch(
        `http://localhost:5001/api/v0/pin/rm?arg=${cid}`,
        {
          method: 'POST',
        }
      );

      if (!response.ok) {
        throw new Error(`Unpin failed: ${response.status}`);
      }
    } catch (error) {
      console.warn('Failed to unpin from local IPFS:', error);
    }
  }

  /**
   * Get gateway URL for a CID
   */
  getGatewayUrl(cid: string): string {
    return `${this.localGateway}/${cid}`;
  }

  /**
   * Check if CID is available
   */
  async isAvailable(cid: string): Promise<boolean> {
    try {
      const response = await fetch(
        `https://nftstorage.link/ipfs/${cid}`,
        {
          method: 'HEAD',
        }
      );
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Get CID metadata
   */
  async getCIDInfo(cid: string): Promise<{
    size: number;
    type: string;
    created?: string;
  }> {
    const response = await this.fetchWithRetry(
      `https://nftstorage.link/ipfs/${cid}`,
      {
        method: 'HEAD',
      }
    );

    if (!response.ok) {
      throw this.createError('GATEWAY_ERROR', `Failed to get info for ${cid}`);
    }

    return {
      size: parseInt(response.headers.get('content-length') || '0', 10),
      type: response.headers.get('content-type') || 'unknown',
      created: response.headers.get('x-ipfs-roots') || undefined,
    };
  }

  /**
   * Fetch with retry logic
   */
  private async fetchWithRetry(
    url: string,
    options: RequestInit,
    retries: number = IPFS_CONFIG.MAX_RETRIES
  ): Promise<Response> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(
          () => controller.abort(),
          IPFS_CONFIG.UPLOAD_TIMEOUT
        );

        const response = await fetch(url, {
          ...options,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);
        return response;
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));

        if (attempt < retries) {
          // Exponential backoff
          const delay = IPFS_CONFIG.RETRY_DELAY * Math.pow(2, attempt);
          await this.sleep(delay);
        }
      }
    }

    throw lastError;
  }

  /**
   * Sleep for specified milliseconds
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Create a typed IPFS error
   */
  private createError(
    code: IPFSError['code'],
    message: string,
    cause?: Error
  ): IPFSError {
    return {
      code,
      message,
      cause,
    };
  }
}

// Export singleton instance
export const ipfsService = new IPFSService();

// Export class for testing
export { IPFSService };

export default ipfsService;
