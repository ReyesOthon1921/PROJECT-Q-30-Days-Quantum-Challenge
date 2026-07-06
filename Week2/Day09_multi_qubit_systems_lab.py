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

def measure_two_qubits_as_q0q1(qc):
    """
    Qiskit prints classical bits from highest index to lowest index.
    To make the output look like q0q1, measure:
    q0 -> c1
    q1 -> c0
    """
    qc.measure(0, 1)
    qc.measure(1, 0)
    return qc

def measure_three_qubits_as_q0q1q2(qc):
    """
    To make the output look like q0q1q2, measure:
    q0 -> c2
    q1 -> c1
    q2 -> c0
    """
    qc.measure(0, 2)
    qc.measure(1, 1)
    qc.measure(2, 0)
    return qc

def save_counts(writer, lab, experiment, description, counts):
    for outcome, count in counts.items():
        writer.writerow(["Day 09", lab, experiment, description, outcome, count])

print("Day 09 Lab: Multi-Qubit Systems")
print("PROJECT-Q 30-Day Quantum Computing Challenge")
print("-" * 70)

# ------------------------------------------------------------
# Lab 1: State-space growth
# Workbook idea:
# Each additional qubit doubles the number of basis states.
# Number of basis states = 2^n
# ------------------------------------------------------------

print("\nLab 1: State-Space Growth")

basis_growth = []

for n in range(1, 8):
    basis_states = 2 ** n
    basis_growth.append((n, basis_states))
    print(f"{n} qubit(s) -> {basis_states} basis states")

# ------------------------------------------------------------
# Lab 2: Two-qubit computational basis states
# Prepare and measure |00>, |01>, |10>, |11>
# ------------------------------------------------------------

print("\nLab 2: Two-Qubit Computational Basis States")

basis_circuits = {
    "00": [],
    "01": [("x", 1)],
    "10": [("x", 0)],
    "11": [("x", 0), ("x", 1)],
}

basis_counts = {}

for label, operations in basis_circuits.items():
    qc = QuantumCircuit(2, 2)

    for gate, qubit in operations:
        if gate == "x":
            qc.x(qubit)

    measure_two_qubits_as_q0q1(qc)
    counts = run_counts(qc, shots)
    basis_counts[label] = counts

    print(f"\nPrepared state |{label}>")
    print(qc.draw(output="text"))
    print("Counts:", counts)

# ------------------------------------------------------------
# Lab 3: Worked example from the workbook
# Start with |00>
# Apply H on q0 and X on q1
# Expected outputs: 01 and 11 with roughly equal probability.
# ------------------------------------------------------------

qc_worked = QuantumCircuit(2, 2)
qc_worked.h(0)
qc_worked.x(1)
measure_two_qubits_as_q0q1(qc_worked)

counts_worked = run_counts(qc_worked, shots)

print("\nLab 3: Worked Example - H on q0 and X on q1")
print(qc_worked.draw(output="text"))
print("Counts:", counts_worked)

# ------------------------------------------------------------
# Lab 4: Three-qubit system
# Apply H gates to all three qubits.
# Expected: all 8 basis states appear with roughly equal probability.
# This demonstrates exponential growth from 2 qubits to 3 qubits.
# ------------------------------------------------------------

qc_three = QuantumCircuit(3, 3)
qc_three.h(0)
qc_three.h(1)
qc_three.h(2)
measure_three_qubits_as_q0q1q2(qc_three)

counts_three = run_counts(qc_three, shots)

print("\nLab 4: Three-Qubit Equal Superposition")
print(qc_three.draw(output="text"))
print("Counts:", counts_three)

# ------------------------------------------------------------
# Lab 5: Compare 2-qubit and 3-qubit result spaces
# 2 qubits can produce 4 possible basis states.
# 3 qubits can produce 8 possible basis states.
# ------------------------------------------------------------

two_qubit_possible_states = 2 ** 2
three_qubit_possible_states = 2 ** 3

print("\nLab 5: Comparing State Spaces")
print("2 qubits possible basis states:", two_qubit_possible_states)
print("3 qubits possible basis states:", three_qubit_possible_states)
print("States observed in Lab 3:", sorted(counts_worked.keys()))
print("States observed in Lab 4:", sorted(counts_three.keys()))

# ------------------------------------------------------------
# Save results
# ------------------------------------------------------------

Path("results/csv").mkdir(parents=True, exist_ok=True)
Path("results/reports").mkdir(parents=True, exist_ok=True)

growth_file = "results/csv/day09_basis_state_growth.csv"
counts_file = "results/csv/day09_multi_qubit_measurements.csv"
report_file = "results/reports/day09_multi_qubit_systems_report.txt"

with open(growth_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "number_of_qubits", "basis_states"])

    for n, basis_states in basis_growth:
        writer.writerow(["Day 09", n, basis_states])

with open(counts_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "lab", "experiment", "description", "outcome", "count"])

    for prepared_state, counts in basis_counts.items():
        save_counts(
            writer,
            "Lab 2",
            "two_qubit_basis_state",
            f"Prepared |{prepared_state}>",
            counts
        )

    save_counts(
        writer,
        "Lab 3",
        "worked_example_h_q0_x_q1",
        "H on q0 creates superposition and X on q1 fixes q1 at 1",
        counts_worked
    )

    save_counts(
        writer,
        "Lab 4",
        "three_qubit_equal_superposition",
        "H on all three qubits creates 8 possible basis states",
        counts_three
    )

with open(report_file, "w") as file:
    file.write("Day 09 Lab: Multi-Qubit Systems\n")
    file.write("PROJECT-Q 30-Day Quantum Computing Challenge\n")
    file.write("=" * 60 + "\n\n")

    file.write("Main ideas:\n")
    file.write("1. Multiple qubits form one combined quantum system.\n")
    file.write("2. Tensor products combine state spaces by multiplication.\n")
    file.write("3. Two qubits have four computational basis states.\n")
    file.write("4. Three qubits have eight computational basis states.\n")
    file.write("5. In general, n qubits have 2^n basis states.\n\n")

    file.write("Basis state growth:\n")
    for n, basis_states in basis_growth:
        file.write(f"{n} qubit(s): {basis_states} basis states\n")

    file.write("\nWorked example counts:\n")
    file.write(str(counts_worked) + "\n\n")

    file.write("Three-qubit superposition counts:\n")
    file.write(str(counts_three) + "\n\n")

    file.write("Lab conclusion:\n")
    file.write("Multi-qubit systems unlock larger quantum state spaces and prepare us for controlled gates, entanglement, and quantum algorithms.\n")

print("\nSaved basis growth to:", growth_file)
print("Saved measurement results to:", counts_file)
print("Saved report to:", report_file)

print("\nLab Summary:")
print("1. One qubit has 2 basis states.")
print("2. Two qubits have 4 basis states.")
print("3. Three qubits have 8 basis states.")
print("4. The number of basis states grows as 2^n.")
print("5. Multi-qubit systems prepare us for CNOT gates, entanglement, and algorithms.")
