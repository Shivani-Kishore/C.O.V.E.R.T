import { groth16 } from 'snarkjs';

export interface ZKProof {
  proof: {
    pi_a: string[];
    pi_b: string[][];
    pi_c: string[];
    protocol: string;
    curve: string;
  };
  publicSignals: string[];
}

export interface HumanityProofInputs {
  secret: string;
  nullifier: string;
  timestamp: number;
}

export interface HumanityProofOutput {
  proof: ZKProof;
  commitment: string;
  nullifierHash: string;
}

export class ZKProofGenerator {
  private wasmPath: string;
  private zkeyPath: string;
  private isInitialized: boolean = false;

  constructor() {
    this.wasmPath = '/circuits/humanity_proof_js/humanity_proof.wasm';
    this.zkeyPath = '/circuits/humanity_proof_final.zkey';
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) return;

    try {
      const wasmResponse = await fetch(this.wasmPath);
      if (!wasmResponse.ok) {
        throw new Error(`Failed to load WASM file: ${this.wasmPath}`);
      }

      const zkeyResponse = await fetch(this.zkeyPath);
      if (!zkeyResponse.ok) {
        throw new Error(`Failed to load zkey file: ${this.zkeyPath}`);
      }

      this.isInitialized = true;
      console.log('ZK Proof Generator initialized');
    } catch (error) {
      console.error('Failed to initialize ZK Proof Generator:', error);
      throw error;
    }
  }

  async generateHumanityProof(inputs: HumanityProofInputs): Promise<HumanityProofOutput> {
    if (!this.isInitialized) {
      await this.initialize();
    }

    try {
      const circuitInputs = {
        secret: this.hashToBigInt(inputs.secret),
        nullifier: this.hashToBigInt(inputs.nullifier),
        timestamp: inputs.timestamp,
      };

      const { proof, publicSignals } = await groth16.fullProve(
        circuitInputs,
        this.wasmPath,
        this.zkeyPath
      );

      const commitment = publicSignals[0];
      const nullifierHash = publicSignals[1];

      return {
        proof: {
          proof: {
            pi_a: proof.pi_a.slice(0, 2),
            pi_b: [
              proof.pi_b[0].slice(0, 2).reverse(),
              proof.pi_b[1].slice(0, 2).reverse(),
            ],
            pi_c: proof.pi_c.slice(0, 2),
            protocol: proof.protocol,
            curve: proof.curve,
          },
          publicSignals,
        },
        commitment,
        nullifierHash,
      };
    } catch (error) {
      console.error('Failed to generate ZK proof:', error);
      throw new Error(`Proof generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  async verifyProof(proof: ZKProof, publicSignals: string[]): Promise<boolean> {
    try {
      const vKeyResponse = await fetch('/circuits/verification_key.json');
      const vKey = await vKeyResponse.json();

      const isValid = await groth16.verify(vKey, publicSignals, proof.proof);
      return isValid;
    } catch (error) {
      console.error('Failed to verify proof:', error);
      return false;
    }
  }

  generateSecret(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
  }

  generateNullifier(secret: string, context: string = 'report'): string {
    return this.hash(`${secret}:${context}:${Date.now()}`);
  }

  private hash(input: string): string {
    const encoder = new TextEncoder();
    const data = encoder.encode(input);

    return crypto.subtle.digest('SHA-256', data).then(buffer => {
      return Array.from(new Uint8Array(buffer))
        .map(byte => byte.toString(16).padStart(2, '0'))
        .join('');
    }).toString();
  }

  private hashToBigInt(input: string): string {
    let hash = 0;
    for (let i = 0; i < input.length; i++) {
      const char = input.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString();
  }

  storeSecret(secret: string): void {
    try {
      localStorage.setItem('zkp_secret', secret);
    } catch (error) {
      console.error('Failed to store secret:', error);
    }
  }

  loadSecret(): string | null {
    try {
      return localStorage.getItem('zkp_secret');
    } catch (error) {
      console.error('Failed to load secret:', error);
      return null;
    }
  }

  clearSecret(): void {
    try {
      localStorage.removeItem('zkp_secret');
    } catch (error) {
      console.error('Failed to clear secret:', error);
    }
  }
}

export const zkProofGenerator = new ZKProofGenerator();
