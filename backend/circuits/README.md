# ZKP Circuits for C.O.V.E.R.T

This directory contains Zero-Knowledge Proof circuits for anonymous authentication.

## Prerequisites

### Install Circom

**Option 1: NPM (Recommended)**
```bash
npm install -g circom
```

**Option 2: Build from source**
```bash
git clone https://github.com/iden3/circom.git
cd circom
cargo build --release
cargo install --path circom
```

### Install SnarkJS
```bash
npm install -g snarkjs
```

## Setup

1. Make the setup script executable:
```bash
chmod +x setup.sh
```

2. Run the setup script:
```bash
./setup.sh
```

This will:
- Compile the humanity_proof circuit
- Download the powers of tau file
- Generate proving and verification keys
- Export a Solidity verifier contract

## Circuit Description

### humanity_proof.circom

Proves that a user is human without revealing their identity.

**Inputs:**
- `secret`: User's secret value (private)
- `nullifier`: Unique value to prevent double-reporting (public)
- `timestamp`: Proof generation timestamp (public)

**Outputs:**
- `commitment`: Hash of secret and timestamp
- `nullifierHash`: Hash of secret and nullifier
- `valid`: Boolean indicating proof validity

## Generated Files

After running setup, you'll have:
- `humanity_proof.r1cs` - Constraint system
- `humanity_proof_js/` - WASM witness generator
- `humanity_proof_final.zkey` - Proving key
- `verification_key.json` - Verification key for backend
- `../contracts/HumanityVerifier.sol` - Solidity verifier contract

## Usage

See the frontend and backend ZKP services for integration examples.
