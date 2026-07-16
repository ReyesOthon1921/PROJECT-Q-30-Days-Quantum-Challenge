# Week 3 Mini Project 3 — Quantum Security Toolkit

## Project-Q 30-Day Quantum Computing Challenge

This project implements an educational Quantum Security Toolkit based on the BB84 Quantum Key Distribution protocol.

The toolkit demonstrates how Alice and Bob can establish a shared secret key and how an eavesdropper named Eve introduces detectable errors through an intercept-and-resend attack.

## Learning Objectives

This project demonstrates:

- Random classical-bit generation
- Random BB84 basis selection
- Quantum-state preparation
- Measurement in the Z and X bases
- Quantum key sifting
- Intercept-and-resend attacks
- Quantum Bit Error Rate calculation
- QBER-based attack detection
- Repeated security experiments
- JSON, CSV, graph, and report generation

## Technology Stack

- Python 3.13.2
- Qiskit 2.5.0
- Qiskit Aer 0.17.2
- Matplotlib 3.11.0
- Visual Studio Code
- Git

## BB84 State Encoding

Alice encodes every classical bit using one of two bases.

| Classical Bit | Basis | Quantum State |
|---|---|---|
| 0 | Z | \|0⟩ |
| 1 | Z | \|1⟩ |
| 0 | X | \|+⟩ |
| 1 | X | \|−⟩ |

Bob independently chooses either the Z or X basis when measuring each qubit.

Alice and Bob publicly compare their basis choices after transmission. They keep only positions where their bases matched. The retained bits form the sifted key.

## Project Files

### `bb84_baseline.py`

Runs BB84 without an eavesdropper.

It demonstrates:

- Alice’s bit and basis generation
- Quantum-state preparation
- Bob’s measurements
- Basis comparison
- Sifted-key generation
- Ideal 0% QBER

### `bb84_eve_attack.py`

Simulates Eve’s intercept-and-resend attack.

Eve:

1. Intercepts Alice’s qubit.
2. Selects a random measurement basis.
3. Measures the qubit.
4. Prepares a replacement qubit.
5. Sends the replacement to Bob.

Incorrect basis choices disturb the transmission and create errors.

### `bb84_security_analysis.py`

Runs repeated experiments with and without Eve.

It produces:

- Trial-level CSV data
- QBER-by-trial graph
- Average-QBER comparison
- Attack-detection-rate graph
- Security-analysis report

### `quantum_security_toolkit.py`

Runs the unified final demonstration.

It:

- Compares secure and attacked channels
- Applies an educational QBER threshold
- Accepts or rejects each session
- Creates sifted-key fingerprints
- Saves JSON and text reports

### `test_quantum_security_toolkit.py`

Tests:

- Random-bit generation
- Random-basis generation
- Secure-channel behavior
- Eve attack detection
- QBER decisions
- Key fingerprints

## Running the Project

Activate the repository environment:

```bat
call .venv-projectq\Scripts\activate