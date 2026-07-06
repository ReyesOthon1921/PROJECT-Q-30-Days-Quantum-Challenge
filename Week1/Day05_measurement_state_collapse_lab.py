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

print("Day 05 Lab: Measurement & State Collapse")
print("PROJECT-Q 30-Day Quantum Computing Challenge")
print("-" * 60)

# Lab 1: Measure the starting |0> state
qc_zero = QuantumCircuit(1, 1)
qc_zero.measure(0, 0)
counts_zero = run_counts(qc_zero, shots)

print("\nLab 1: Measuring the starting |0> state")
print(qc_zero)
print("Counts:", counts_zero)

# Lab 2: Create superposition, then measure
qc_superposition = QuantumCircuit(1, 1)
qc_superposition.h(0)
qc_superposition.measure(0, 0)
counts_superposition = run_counts(qc_superposition, shots)

print("\nLab 2: Measuring a qubit after Hadamard superposition")
print(qc_superposition)
print("Counts:", counts_superposition)

# Lab 3: Measure the same qubit twice
qc_repeat = QuantumCircuit(1, 2)
qc_repeat.h(0)
qc_repeat.measure(0, 0)
qc_repeat.measure(0, 1)
counts_repeat = run_counts(qc_repeat, shots)

print("\nLab 3: Measuring the same qubit twice")
print(qc_repeat)
print("Counts:", counts_repeat)

# Lab 4: Measure at the end after H then H
qc_measure_end = QuantumCircuit(1, 1)
qc_measure_end.h(0)
qc_measure_end.h(0)
qc_measure_end.measure(0, 0)
counts_measure_end = run_counts(qc_measure_end, shots)

print("\nLab 4: Measuring at the end after H then H")
print(qc_measure_end)
print("Counts:", counts_measure_end)

Path("results/csv").mkdir(parents=True, exist_ok=True)

output_file = "results/csv/day05_measurement_state_collapse_lab.csv"

with open(output_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "lab", "concept", "outcome", "count"])

    for outcome, count in counts_zero.items():
        writer.writerow(["Day 05", "Lab 1", "measure_starting_zero_state", outcome, count])

    for outcome, count in counts_superposition.items():
        writer.writerow(["Day 05", "Lab 2", "measure_superposition_statistics", outcome, count])

    for outcome, count in counts_repeat.items():
        writer.writerow(["Day 05", "Lab 3", "measure_twice_state_collapse", outcome, count])

    for outcome, count in counts_measure_end.items():
        writer.writerow(["Day 05", "Lab 4", "measure_at_the_end", outcome, count])

print("\nSaved lab results to:", output_file)

print("\nLab Summary:")
print("1. Measuring |0> gives a classical 0 result.")
print("2. Measuring superposition gives probabilistic results over many shots.")
print("3. Measuring twice gives the same result because the state has collapsed.")
print("4. Measuring at the end lets the circuit finish before producing a classical output.")
