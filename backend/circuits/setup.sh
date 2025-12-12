#!/bin/bash

set -e

echo "ZKP Circuit Setup Script"
echo "======================="

CIRCUIT_NAME="humanity_proof"
PTAU_FILE="powersOfTau28_hez_final_12.ptau"

if ! command -v circom &> /dev/null; then
    echo "Error: circom not found. Please install Circom first:"
    echo "  npm install -g circom"
    echo "  Or download from: https://docs.circom.io/getting-started/installation/"
    exit 1
fi

echo "1. Compiling circuit..."
circom ${CIRCUIT_NAME}.circom --r1cs --wasm --sym --c

if [ ! -f "$PTAU_FILE" ]; then
    echo "2. Downloading powers of tau file..."
    wget https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_12.ptau
fi

echo "3. Generating proving key..."
npx snarkjs groth16 setup ${CIRCUIT_NAME}.r1cs $PTAU_FILE ${CIRCUIT_NAME}_0000.zkey

echo "4. Contributing to the ceremony..."
npx snarkjs zkey contribute ${CIRCUIT_NAME}_0000.zkey ${CIRCUIT_NAME}_final.zkey --name="1st Contributor" -e="random entropy"

echo "5. Exporting verification key..."
npx snarkjs zkey export verificationkey ${CIRCUIT_NAME}_final.zkey verification_key.json

echo "6. Exporting Solidity verifier..."
npx snarkjs zkey export solidityverifier ${CIRCUIT_NAME}_final.zkey ../contracts/HumanityVerifier.sol

echo "7. Cleaning up intermediate files..."
rm ${CIRCUIT_NAME}_0000.zkey

echo ""
echo "Setup complete!"
echo "Files generated:"
echo "  - ${CIRCUIT_NAME}.r1cs (constraint system)"
echo "  - ${CIRCUIT_NAME}_js/ (WASM witness generator)"
echo "  - ${CIRCUIT_NAME}_final.zkey (proving key)"
echo "  - verification_key.json (verification key)"
echo "  - ../contracts/HumanityVerifier.sol (Solidity verifier)"
