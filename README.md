# zk-ScalHard: Project Implementation Artifacts

This folder contains the source code, arithmetic circuits, and benchmarking scripts for the **zk-ScalHard** protocol.

## 1. Directory Structure
- `ZonalIntegrity/`: Tier-1 ZK-circuit logic and ZCU-level attestation.
- `HPCAggregation/`: Tier-2 Recursive ZK-aggregation and vehicle-level proof.
- `Figures/`: Python scripts to reproduce the scalability and security graphs.

## 2. Prerequisites
- **Circom 2.1.6**
- **SnarkJS 0.7.0**
- **Node.js v18.19.1+**
- **Python 3.10+** (with `matplotlib` and `numpy`)

## 3. Execution Guide

### Tier-1: Zonal Identity and Integrity (ZIDI)
Navigate to the `ZonalIntegrity` folder and run:
```bash
# 1. Install dependencies
npm install circomlib

# 2. Compile Circuit
circom ZonalIntegrity.circom --r1cs --wasm --sym

# 3. Trusted Setup (Factory Enrollment Simulation)
snarkjs groth16 setup ZonalIntegrity.r1cs pot14_final.ptau zonal_0000.zkey
snarkjs zkey contribute zonal_0000.zkey zonal_final.zkey --name="Contributor_1" -v
snarkjs zkey export verificationkey zonal_final.zkey verification_key.json

# 4. Runtime Handshake (Benchmark)
node ZonalIntegrity_js/generate_witness.js ZonalIntegrity_js/ZonalIntegrity.wasm input.json witness.wtns
snarkjs groth16 prove zonal_final.zkey witness.wtns proof.json public.json
snarkjs groth16 verify verification_key.json public.json proof.json
```
### Tier-2: HPC Aggregation (HPCA)
Navigate to the HPCAggregation folder and run:
```bash
# 1. Compile and Setup
circom HPC_Aggregator.circom --r1cs --wasm --sym
snarkjs groth16 setup HPC_Aggregator.r1cs pot14_final.ptau hpc_0000.zkey
snarkjs zkey contribute hpc_0000.zkey hpc_final.zkey --name="Contributor_2" -v
snarkjs zkey export verificationkey hpc_final.zkey hpc_verification_key.json

# 2. Aggregation Handshake (Benchmark)
node HPC_Aggregator_js/generate_witness.js HPC_Aggregator_js/HPC_Aggregator.wasm input.json hpc_witness.wtns
snarkjs groth16 prove hpc_final.zkey hpc_witness.wtns hpc_proof.json hpc_public.json
snarkjs groth16 verify hpc_verification_key.json hpc_public.json hpc_proof.json
```

## 4. Reproducing Figures
Navigate to the Figures folder and execute the scripts to generate the paper's results:
```bash
python3 final_bandwidth_graph.py           # Reproduces Figure 8
python3 final_verification_latency_100.py  # Reproduces Figure 9
python3 temporal_isolation.py              # Reproduces Figure 10
```
