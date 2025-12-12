import { useState, useEffect } from 'react';
import { zkProofGenerator, ZKProof, HumanityProofOutput } from './proofGenerator';

export interface UseZKProofResult {
  isInitialized: boolean;
  isGenerating: boolean;
  error: string | null;
  secret: string | null;
  generateProof: (nullifier?: string) => Promise<HumanityProofOutput | null>;
  verifyProof: (proof: ZKProof, publicSignals: string[]) => Promise<boolean>;
  initializeSecret: () => string;
  loadSecret: () => string | null;
  clearSecret: () => void;
}

export function useZKProof(): UseZKProofResult {
  const [isInitialized, setIsInitialized] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [secret, setSecret] = useState<string | null>(null);

  useEffect(() => {
    const initializeGenerator = async () => {
      try {
        await zkProofGenerator.initialize();
        setIsInitialized(true);

        const existingSecret = zkProofGenerator.loadSecret();
        if (existingSecret) {
          setSecret(existingSecret);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to initialize ZK proof generator');
        console.error('ZKP initialization error:', err);
      }
    };

    initializeGenerator();
  }, []);

  const initializeSecret = (): string => {
    const newSecret = zkProofGenerator.generateSecret();
    zkProofGenerator.storeSecret(newSecret);
    setSecret(newSecret);
    return newSecret;
  };

  const loadSecret = (): string | null => {
    const loadedSecret = zkProofGenerator.loadSecret();
    setSecret(loadedSecret);
    return loadedSecret;
  };

  const clearSecret = (): void => {
    zkProofGenerator.clearSecret();
    setSecret(null);
  };

  const generateProof = async (nullifier?: string): Promise<HumanityProofOutput | null> => {
    if (!isInitialized) {
      setError('ZK proof generator not initialized');
      return null;
    }

    let currentSecret = secret;
    if (!currentSecret) {
      currentSecret = initializeSecret();
    }

    setIsGenerating(true);
    setError(null);

    try {
      const nullifierValue = nullifier || zkProofGenerator.generateNullifier(currentSecret);
      const timestamp = Math.floor(Date.now() / 1000);

      const proofOutput = await zkProofGenerator.generateHumanityProof({
        secret: currentSecret,
        nullifier: nullifierValue,
        timestamp,
      });

      setIsGenerating(false);
      return proofOutput;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate proof';
      setError(errorMessage);
      setIsGenerating(false);
      console.error('Proof generation error:', err);
      return null;
    }
  };

  const verifyProof = async (proof: ZKProof, publicSignals: string[]): Promise<boolean> => {
    try {
      return await zkProofGenerator.verifyProof(proof, publicSignals);
    } catch (err) {
      console.error('Proof verification error:', err);
      return false;
    }
  };

  return {
    isInitialized,
    isGenerating,
    error,
    secret,
    generateProof,
    verifyProof,
    initializeSecret,
    loadSecret,
    clearSecret,
  };
}
