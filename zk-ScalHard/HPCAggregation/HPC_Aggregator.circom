pragma circom 2.0.0;
include "node_modules/circomlib/circuits/poseidon.circom";

template HPCAggregator() {
    // PRIVATE INPUTS
    signal input hpc_puf_witness;
    signal input zonal_roots[4]; // The 4 roots from your 4 ZCUs

    // PUBLIC INPUTS
    signal input public_vehicle_id;
    signal input public_global_root;

    // 1. HPC IDENTITY CHECK
    component hpcHasher = Poseidon(1);
    hpcHasher.inputs[0] <== hpc_puf_witness;
    // Benchmarking soft constraint
    signal hpc_id_check <== hpcHasher.out * public_vehicle_id;

    // 2. GLOBAL AGGREGATION CHECK
    component globalHasher = Poseidon(4);
    for (var i = 0; i < 4; i++) {
        globalHasher.inputs[i] <== zonal_roots[i];
    }
    // Benchmarking soft constraint
    signal global_root_check <== globalHasher.out * public_global_root;
}

component main {public [public_vehicle_id, public_global_root]} = HPCAggregator();