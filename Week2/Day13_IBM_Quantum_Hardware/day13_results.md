# Day 13 - IBM Quantum Hardware Lab Results

Completed: 2026-07-06 12:28:22

## Lab Focus

This lab demonstrates how a quantum program is written in Python, converted into a Qiskit circuit, transpiled for a backend, executed, and returned as classical measurement counts.

## Circuit

The circuit creates a Bell state using:

- Hadamard gate on qubit 0
- CNOT gate from qubit 0 to qubit 1
- Measurement of both qubits

## Backend

Local Qiskit AerSimulator

## Shots

1024

## Counts

`{'11': 507, '00': 517}`

## Percentages

- `00`: 50.49%
- `11`: 49.51%

## Interpretation

The expected Bell-state result is mostly `00` and `11`. On an ideal simulator, the results should be close to a 50/50 split. On real IBM Quantum hardware, small amounts of `01` and `10` may appear because of noise, decoherence, gate errors, and measurement errors.
