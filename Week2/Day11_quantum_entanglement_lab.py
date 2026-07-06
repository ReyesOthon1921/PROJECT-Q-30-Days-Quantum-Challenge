from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import csv
from pathlib import Path

shots = 1000
simulator = AerSimulator()

def run_counts(circuit, shots=1000):
    compiled = transpile(circuit, simulator)
    result = simulator.run(compiled, shots=shots).result()
    return result.get_counts()

def measure_control_target(qc):
    """
    q0 = first qubit
    q1 = second qubit

    Qiskit prints classical bits from highest index to lowest index.
    To make the printed result look like q0q1, measure:
    q0 -> c1
    q1 -> c0
    """
    qc.measure(0, 1)
    qc.measure(1, 0)
    return qc

def save_counts(writer, lab, experiment, description, counts):
    for outcome, count in counts.items():
        writer.writerow(["Day 11", lab, experiment, description, outcome, count])

print("Day 11 Lab: Quantum Entanglement")
print("PROJECT-Q 30-Day Quantum Computing Challenge")
print("-" * 60)

# ------------------------------------------------------------
# Lab 1: Create the first Bell state using H + CNOT
# Workbook idea:
# H creates superposition on q0.
# CNOT links q1 to q0.
# Expected ideal measurement pattern: mostly 00 and 11.
# ------------------------------------------------------------

qc_bell = QuantumCircuit(2, 2)
qc_bell.h(0)
qc_bell.cx(0, 1)
measure_control_target(qc_bell)

counts_bell = run_counts(qc_bell, shots)

print("\nLab 1: Create Bell State with H + CNOT")
print(qc_bell.draw(output="text"))
print("Counts:", counts_bell)

# ------------------------------------------------------------
# Lab 2: CNOT alone does not always create entanglement
# Workbook idea:
# If the control is not in superposition, CNOT alone does not create the Bell state.
# Starting from |00>, CNOT still gives |00>.
# ------------------------------------------------------------

qc_cnot_alone = QuantumCircuit(2, 2)
qc_cnot_alone.cx(0, 1)
measure_control_target(qc_cnot_alone)

counts_cnot_alone = run_counts(qc_cnot_alone, shots)

print("\nLab 2: CNOT Alone from |00>")
print(qc_cnot_alone.draw(output="text"))
print("Counts:", counts_cnot_alone)

# ------------------------------------------------------------
# Lab 3: Superposition without CNOT
# Workbook idea:
# A single qubit can be in superposition, but that is not the same as entanglement.
# H on q0 creates randomness for q0, while q1 remains 0.
# Expected pattern: mostly 00 and 10.
# ------------------------------------------------------------

qc_superposition_only = QuantumCircuit(2, 2)
qc_superposition_only.h(0)
measure_control_target(qc_superposition_only)

counts_superposition_only = run_counts(qc_superposition_only, shots)

print("\nLab 3: Superposition Only, No Entanglement")
print(qc_superposition_only.draw(output="text"))
print("Counts:", counts_superposition_only)

# ------------------------------------------------------------
# Lab 4: Create a different Bell-style correlation
# Start with q1 flipped, then apply H + CNOT.
# Expected ideal measurement pattern: mostly 01 and 10.
# This shows different entangled states can produce different correlations.
# ------------------------------------------------------------

qc_opposite_correlation = QuantumCircuit(2, 2)
qc_opposite_correlation.x(1)
qc_opposite_correlation.h(0)
qc_opposite_correlation.cx(0, 1)
measure_control_target(qc_opposite_correlation)

counts_opposite_correlation = run_counts(qc_opposite_correlation, shots)

print("\nLab 4: Opposite Correlation Bell Pattern")
print(qc_opposite_correlation.draw(output="text"))
print("Counts:", counts_opposite_correlation)

# ------------------------------------------------------------
# Lab 5: Correlation check for the first Bell state
# In the first Bell state, 00 and 11 are correlated results.
# 01 and 10 should not appear in an ideal simulator.
# ------------------------------------------------------------

correlated = counts_bell.get("00", 0) + counts_bell.get("11", 0)
uncorrelated = counts_bell.get("01", 0) + counts_bell.get("10", 0)

print("\nLab 5: Bell State Correlation Check")
print("Correlated counts 00 + 11:", correlated)
print("Uncorrelated counts 01 + 10:", uncorrelated)
print("Total shots:", shots)

# ------------------------------------------------------------
# Save results
# ------------------------------------------------------------

Path("results/csv").mkdir(parents=True, exist_ok=True)

output_file = "results/csv/day11_quantum_entanglement_lab.csv"

with open(output_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "lab", "experiment", "description", "outcome", "count"])

    save_counts(
        writer,
        "Lab 1",
        "bell_state_h_then_cnot",
        "H creates superposition and CNOT creates entanglement",
        counts_bell
    )

    save_counts(
        writer,
        "Lab 2",
        "cnot_alone",
        "CNOT alone from |00> does not create Bell-state randomness",
        counts_cnot_alone
    )

    save_counts(
        writer,
        "Lab 3",
        "superposition_without_cnot",
        "H alone creates superposition but not entanglement",
        counts_superposition_only
    )

    save_counts(
        writer,
        "Lab 4",
        "opposite_correlation_bell_pattern",
        "Different Bell-style preparation gives opposite correlation",
        counts_opposite_correlation
    )

    writer.writerow([
        "Day 11",
        "Lab 5",
        "correlation_check",
        "Bell state correlated outcomes 00 and 11",
        "correlated_00_plus_11",
        correlated
    ])

    writer.writerow([
        "Day 11",
        "Lab 5",
        "correlation_check",
        "Bell state uncorrelated outcomes 01 and 10",
        "uncorrelated_01_plus_10",
        uncorrelated
    ])

print("\nSaved lab results to:", output_file)

print("\nLab Summary:")
print("1. Entanglement is created by combining H and CNOT.")
print("2. The first Bell state gives correlated outcomes: 00 and 11.")
print("3. CNOT alone does not always create entanglement.")
print("4. Superposition by itself is not the same as entanglement.")
print("5. Entanglement describes the shared state of the two-qubit system.")
