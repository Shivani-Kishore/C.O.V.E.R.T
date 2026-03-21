/**
 * Type stub for snarkjs (no official @types package).
 * Add more specific types as the ZKP feature is built out.
 */
declare module 'snarkjs' {
    export const groth16: {
        fullProve(
            input: Record<string, unknown>,
            wasmFile: string,
            zkeyFile: string
        ): Promise<{ proof: ZKProofInternal; publicSignals: string[] }>;
        verify(
            vKey: Record<string, unknown>,
            publicSignals: string[],
            proof: ZKProofInternal
        ): Promise<boolean>;
        exportSolidityCallData(
            proof: ZKProofInternal,
            publicSignals: string[]
        ): Promise<string>;
    };

    interface ZKProofInternal {
        pi_a: string[];
        pi_b: string[][];
        pi_c: string[];
        protocol: string;
        curve: string;
    }
}
