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

def make_cnot_truth_table_circuit(control_value, target_value):
    """
    q0 = control qubit
    q1 = target qubit

    Important:
    Qiskit prints classical bits from highest index to lowest index.
    To make the printed result look like ControlTarget, we measure:
    q0 -> c1
    q1 -> c0
    """
    qc = QuantumCircuit(2, 2)

    if control_value == 1:
        qc.x(0)

    if target_value == 1:
        qc.x(1)

    qc.cx(0, 1)

    qc.measure(0, 1)
    qc.measure(1, 0)

    return qc

print("Day 10 Lab: Controlled-NOT (CNOT) Gate")
print("PROJECT-Q 30-Day Quantum Computing Challenge")
print("-" * 60)

# ------------------------------------------------------------
# Lab 1: CNOT truth table
# Workbook idea:
# If control = 0, target does not flip.
# If control = 1, target flips.
# ------------------------------------------------------------

truth_table_inputs = [
    (0, 0),
    (0, 1),
    (1, 0),
    (1, 1),
]

truth_table_results = []

print("\nLab 1: CNOT Truth Table")

for control_value, target_value in truth_table_inputs:
    qc = make_cnot_truth_table_circuit(control_value, target_value)
    counts = run_counts(qc, shots)
    measured_output = max(counts, key=counts.get)

    input_state = f"{control_value}{target_value}"

    print(f"\nInput ControlTarget: {input_state}")
    print(qc.draw(output="text"))
    print("Counts:", counts)
    print("Most likely output:", measured_output)

    truth_table_results.append({
        "lab": "Lab 1",
        "experiment": "cnot_truth_table",
        "input": input_state,
        "output": measured_output,
        "counts": counts,
    })

# ------------------------------------------------------------
# Lab 2: Workbook example
# Start at |00>, apply X to control, then CNOT.
# Expected final result: |11>
# ------------------------------------------------------------

qc_example = QuantumCircuit(2, 2)

qc_example.x(0)       # Prepare control qubit as 1
qc_example.cx(0, 1)   # Control q0, target q1

# Measure so displayed string is ControlTarget
qc_example.measure(0, 1)
qc_example.measure(1, 0)

counts_example = run_counts(qc_example, shots)

print("\nLab 2: Workbook Example - X on control, then CNOT")
print(qc_example.draw(output="text"))
print("Counts:", counts_example)

# ------------------------------------------------------------
# Lab 3: Target does not flip when control is 0
# Start at |01>, then apply CNOT.
# Expected result: |01>
# ------------------------------------------------------------

qc_control_zero = QuantumCircuit(2, 2)

qc_control_zero.x(1)      # Target starts as 1, control stays 0
qc_control_zero.cx(0, 1)

qc_control_zero.measure(0, 1)
qc_control_zero.measure(1, 0)

counts_control_zero = run_counts(qc_control_zero, shots)

print("\nLab 3: Control is 0, so target does not flip")
print(qc_control_zero.draw(output="text"))
print("Counts:", counts_control_zero)

# ------------------------------------------------------------
# Lab 4: Create a Bell state using H + CNOT
# Workbook idea:
# CNOT is foundational for entanglement.
# H creates superposition on the control qubit.
# CNOT links the target to the control.
# Expected measurement pattern: mostly 00 and 11.
# ------------------------------------------------------------

qc_bell = QuantumCircuit(2, 2)

qc_bell.h(0)
qc_bell.cx(0, 1)

qc_bell.measure(0, 1)
qc_bell.measure(1, 0)

counts_bell = run_counts(qc_bell, shots)

print("\nLab 4: Bell State Demo using H + CNOT")
print(qc_bell.draw(output="text"))
print("Counts:", counts_bell)

# ------------------------------------------------------------
# Save results
# ------------------------------------------------------------

Path("results/csv").mkdir(parents=True, exist_ok=True)

output_file = "results/csv/day10_cnot_gate_lab.csv"

with open(output_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "lab", "experiment", "input_state", "outcome", "count"])

    for item in truth_table_results:
        for outcome, count in item["counts"].items():
            writer.writerow([
                "Day 10",
                item["lab"],
                item["experiment"],
                item["input"],
                outcome,
                count
            ])

    for outcome, count in counts_example.items():
        writer.writerow(["Day 10", "Lab 2", "workbook_x_control_then_cnot", "00_then_X_control", outcome, count])

    for outcome, count in counts_control_zero.items():
        writer.writerow(["Day 10", "Lab 3", "control_zero_target_unchanged", "01", outcome, count])

    for outcome, count in counts_bell.items():
        writer.writerow(["Day 10", "Lab 4", "bell_state_h_then_cnot", "superposition_control", outcome, count])

print("\nSaved lab results to:", output_file)

print("\nLab Summary:")
print("1. CNOT uses a control qubit and a target qubit.")
print("2. If the control qubit is 0, the target does not flip.")
print("3. If the control qubit is 1, the target flips.")
print("4. CNOT is a two-qubit gate that lets qubits interact.")
print("5. H followed by CNOT can create a Bell-state measurement pattern.")
