pragma circom 2.0.0;

include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/comparators.circom";

template HumanityProof() {
    signal input secret;
    signal input nullifier;
    signal input timestamp;
    signal output commitment;
    signal output nullifierHash;
    signal output valid;

    component hasher1 = Poseidon(2);
    hasher1.inputs[0] <== secret;
    hasher1.inputs[1] <== timestamp;
    commitment <== hasher1.out;

    component hasher2 = Poseidon(2);
    hasher2.inputs[0] <== secret;
    hasher2.inputs[1] <== nullifier;
    nullifierHash <== hasher2.out;

    component timestampCheck = LessThan(64);
    timestampCheck.in[0] <== 1700000000;
    timestampCheck.in[1] <== timestamp;

    valid <== timestampCheck.out;
}

component main {public [nullifier, timestamp]} = HumanityProof();
