from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector
import csv
from pathlib import Path

shots = 1000
simulator = AerSimulator()

def run_counts(circuit, shots=1000):
    compiled = transpile(circuit, simulator)
    result = simulator.run(compiled, shots=shots).result()
    return result.get_counts()

def show_state(label, circuit_without_measurement):
    state = Statevector.from_instruction(circuit_without_measurement)
    probabilities = state.probabilities_dict()

    print(f"\n{label}")
    print(circuit_without_measurement.draw(output="text"))
    print("Statevector:", state)
    print("Probabilities:", probabilities)

print("Day 06 Lab: Single-Qubit Quantum Gates")
print("PROJECT-Q 30-Day Quantum Computing Challenge")
print("-" * 60)

# ------------------------------------------------------------
# Lab 1: X Gate
# Workbook idea: X acts like a NOT gate for basis states.
# It flips |0> to |1>.
# ------------------------------------------------------------

qc_x_state = QuantumCircuit(1)
qc_x_state.x(0)
show_state("Lab 1 State: X Gate on |0>", qc_x_state)

qc_x_measure = QuantumCircuit(1, 1)
qc_x_measure.x(0)
qc_x_measure.measure(0, 0)
counts_x = run_counts(qc_x_measure, shots)

print("\nLab 1 Measurement: X Gate")
print(qc_x_measure.draw(output="text"))
print("Counts:", counts_x)

# ------------------------------------------------------------
# Lab 2: Y Gate
# Workbook idea: Y flips the qubit and also changes phase.
# Measurement looks like a flip, but the statevector shows phase.
# ------------------------------------------------------------

qc_y_state = QuantumCircuit(1)
qc_y_state.y(0)
show_state("Lab 2 State: Y Gate on |0>", qc_y_state)

qc_y_measure = QuantumCircuit(1, 1)
qc_y_measure.y(0)
qc_y_measure.measure(0, 0)
counts_y = run_counts(qc_y_measure, shots)

print("\nLab 2 Measurement: Y Gate")
print(qc_y_measure.draw(output="text"))
print("Counts:", counts_y)

# ------------------------------------------------------------
# Lab 3: Z Gate on |0>
# Workbook idea: Z does not swap |0> and |1>.
# On |0>, measurement still gives 0.
# ------------------------------------------------------------

qc_z_zero_state = QuantumCircuit(1)
qc_z_zero_state.z(0)
show_state("Lab 3 State: Z Gate on |0>", qc_z_zero_state)

qc_z_zero_measure = QuantumCircuit(1, 1)
qc_z_zero_measure.z(0)
qc_z_zero_measure.measure(0, 0)
counts_z_zero = run_counts(qc_z_zero_measure, shots)

print("\nLab 3 Measurement: Z Gate on |0>")
print(qc_z_zero_measure.draw(output="text"))
print("Counts:", counts_z_zero)

# ------------------------------------------------------------
# Lab 4: Hadamard Gate
# Workbook idea: H creates equal superposition.
# Measurement should be close to 50/50 after many shots.
# ------------------------------------------------------------

qc_h_state = QuantumCircuit(1)
qc_h_state.h(0)
show_state("Lab 4 State: Hadamard Gate on |0>", qc_h_state)

qc_h_measure = QuantumCircuit(1, 1)
qc_h_measure.h(0)
qc_h_measure.measure(0, 0)
counts_h = run_counts(qc_h_measure, shots)

print("\nLab 4 Measurement: Hadamard Gate")
print(qc_h_measure.draw(output="text"))
print("Counts:", counts_h)

# ------------------------------------------------------------
# Lab 5: Why phase matters
# Workbook idea: Z may not immediately change measurement probabilities,
# but phase affects later operations and interference.
#
# H then H returns |0>.
# H then Z then H changes the final result to |1>.
# ------------------------------------------------------------

qc_hh = QuantumCircuit(1, 1)
qc_hh.h(0)
qc_hh.h(0)
qc_hh.measure(0, 0)
counts_hh = run_counts(qc_hh, shots)

qc_hzh = QuantumCircuit(1, 1)
qc_hzh.h(0)
qc_hzh.z(0)
qc_hzh.h(0)
qc_hzh.measure(0, 0)
counts_hzh = run_counts(qc_hzh, shots)

print("\nLab 5A: H then H")
print(qc_hh.draw(output="text"))
print("Counts:", counts_hh)

print("\nLab 5B: H then Z then H")
print(qc_hzh.draw(output="text"))
print("Counts:", counts_hzh)

# ------------------------------------------------------------
# Save results
# ------------------------------------------------------------

Path("results/csv").mkdir(parents=True, exist_ok=True)

output_file = "results/csv/day06_single_qubit_gates_lab.csv"

with open(output_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "lab", "gate_or_experiment", "concept", "outcome", "count"])

    for outcome, count in counts_x.items():
        writer.writerow(["Day 06", "Lab 1", "X", "bit_flip", outcome, count])

    for outcome, count in counts_y.items():
        writer.writerow(["Day 06", "Lab 2", "Y", "bit_flip_plus_phase", outcome, count])

    for outcome, count in counts_z_zero.items():
        writer.writerow(["Day 06", "Lab 3", "Z", "phase_gate_on_zero_state", outcome, count])

    for outcome, count in counts_h.items():
        writer.writerow(["Day 06", "Lab 4", "H", "creates_superposition", outcome, count])

    for outcome, count in counts_hh.items():
        writer.writerow(["Day 06", "Lab 5A", "H_then_H", "interference_without_z_phase", outcome, count])

    for outcome, count in counts_hzh.items():
        writer.writerow(["Day 06", "Lab 5B", "H_then_Z_then_H", "z_phase_affects_interference", outcome, count])

print("\nSaved lab results to:", output_file)

print("\nLab Summary:")
print("1. X flips |0> to |1>.")
print("2. Y flips the qubit and introduces phase.")
print("3. Z changes phase, even if measurement probabilities may look unchanged.")
print("4. H creates superposition, giving close to 50/50 results over many shots.")
print("5. Phase matters because it affects later interference.")
