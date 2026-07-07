"""
Day 08 — Qiskit Architecture Lab

Goal:
Show how a quantum program moves through the Qiskit workflow:

Python program
-> Qiskit QuantumCircuit
-> Transpiler
-> Backend / Simulator
-> Measurement results
-> Analysis
-> CSV and text report outputs
"""

from pathlib import Path
import csv
from datetime import datetime

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


# -----------------------------
# Output folders
# -----------------------------

RESULTS_DIR = Path("results")
CSV_DIR = RESULTS_DIR / "csv"
REPORTS_DIR = RESULTS_DIR / "reports"

CSV_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


COUNTS_CSV = CSV_DIR / "day08_qiskit_architecture_counts.csv"
LAYERS_CSV = CSV_DIR / "day08_qiskit_architecture_layers.csv"
REPORT_TXT = REPORTS_DIR / "day08_qiskit_architecture_report.txt"


# -----------------------------
# Layer 1: Python Program
# -----------------------------

print("\nDay 08 — Qiskit Architecture Lab")
print("=" * 40)

print("\nLayer 1: Python Program")
print("The user writes Python code to describe a quantum circuit.")


# -----------------------------
# Layer 2: Qiskit SDK / Circuit
# -----------------------------

print("\nLayer 2: Qiskit SDK / QuantumCircuit")
print("Qiskit creates qubits, gates, circuits, and measurements.")

qc = QuantumCircuit(2, 2)

# Create a Bell state:
# 1. Hadamard puts qubit 0 into superposition.
# 2. CNOT entangles qubit 0 with qubit 1.
# 3. Measurement reads both qubits.
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

print("\nOriginal circuit:")
print(qc.draw(output="text"))


# -----------------------------
# Layer 3: Transpiler
# -----------------------------

print("\nLayer 3: Transpiler")
print("The transpiler prepares and optimizes the circuit for the selected backend.")

backend = AerSimulator()

transpiled_level_0 = transpile(qc, backend=backend, optimization_level=0)
transpiled_level_3 = transpile(qc, backend=backend, optimization_level=3)

print("\nTranspiled circuit with optimization_level=0:")
print(transpiled_level_0.draw(output="text"))

print("\nTranspiled circuit with optimization_level=3:")
print(transpiled_level_3.draw(output="text"))

level_0_depth = transpiled_level_0.depth()
level_0_size = transpiled_level_0.size()
level_0_ops = transpiled_level_0.count_ops()

level_3_depth = transpiled_level_3.depth()
level_3_size = transpiled_level_3.size()
level_3_ops = transpiled_level_3.count_ops()

print(f"\nOptimization level 0 depth: {level_0_depth}")
print(f"Optimization level 0 size: {level_0_size}")
print(f"Optimization level 0 operations: {dict(level_0_ops)}")

print(f"Optimization level 3 depth: {level_3_depth}")
print(f"Optimization level 3 size: {level_3_size}")
print(f"Optimization level 3 operations: {dict(level_3_ops)}")


# -----------------------------
# Layer 4: Backend
# -----------------------------

print("\nLayer 4: Backend")
print(f"Backend used: {backend.name}")
print("Backend type: Simulator")
print("Simulators are useful for learning, debugging, and testing circuits.")


# -----------------------------
# Layer 5: Measurement Results
# -----------------------------

print("\nLayer 5: Measurement Results")

shots = 1000
job = backend.run(transpiled_level_3, shots=shots)
result = job.result()
counts = result.get_counts()

print(f"Shots: {shots}")
print(f"Counts: {counts}")


# -----------------------------
# Layer 6: Analysis
# -----------------------------

print("\nLayer 6: Analysis")

count_00 = counts.get("00", 0)
count_01 = counts.get("01", 0)
count_10 = counts.get("10", 0)
count_11 = counts.get("11", 0)

correlated = count_00 + count_11
uncorrelated = count_01 + count_10

print(f"Correlated outcomes 00 + 11: {correlated}")
print(f"Uncorrelated outcomes 01 + 10: {uncorrelated}")

if correlated > uncorrelated:
    interpretation = (
        "The Bell-state circuit produced mostly correlated outcomes. "
        "This is expected because the Hadamard plus CNOT gates create entanglement."
    )
else:
    interpretation = (
        "The output did not show the expected Bell-state correlation. "
        "This should be checked again."
    )

print(f"Interpretation: {interpretation}")


# -----------------------------
# Save CSV outputs
# -----------------------------

with open(COUNTS_CSV, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "lab", "backend", "shots", "outcome", "count"])

    for outcome, count in sorted(counts.items()):
        writer.writerow([
            "Day 08",
            "Qiskit Architecture",
            backend.name,
            shots,
            outcome,
            count,
        ])

with open(LAYERS_CSV, "w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "layer", "component", "description"])

    rows = [
        [
            "Day 08",
            "Layer 1",
            "Python Program",
            "User writes Python code to describe the circuit",
        ],
        [
            "Day 08",
            "Layer 2",
            "Qiskit SDK",
            "Qiskit creates qubits, gates, circuits, and measurements",
        ],
        [
            "Day 08",
            "Layer 3",
            "Transpiler",
            "Prepares and optimizes the circuit for the selected backend",
        ],
        [
            "Day 08",
            "Layer 4",
            "Backend",
            "Simulator or real quantum hardware executes the circuit",
        ],
        [
            "Day 08",
            "Layer 5",
            "Results",
            "Measurement counts are returned after execution",
        ],
        [
            "Day 08",
            "Layer 6",
            "Analysis",
            "Counts are interpreted and compared",
        ],
    ]

    writer.writerows(rows)


# -----------------------------
# Save text report
# -----------------------------

original_circuit_text = """
q0: --H----●----M--
           |
q1: -------X----M--

This creates a Bell-state circuit:
1. H gate creates superposition on q0.
2. CX/CNOT entangles q0 with q1.
3. Both qubits are measured.
"""

level_0_circuit_text = original_circuit_text
level_3_circuit_text = original_circuit_text

with open(REPORT_TXT, "w", encoding="utf-8") as file:
    file.write("Day 08 — Qiskit Architecture Lab Report\n")
    file.write("=" * 45 + "\n\n")

    file.write(f"Generated: {datetime.now()}\n\n")

    file.write("Purpose\n")
    file.write("-" * 20 + "\n")
    file.write(
        "This lab explains the Qiskit workflow from Python code to a quantum "
        "circuit, transpilation, backend execution, measurement results, and analysis.\n\n"
    )

    file.write("Original Circuit\n")
    file.write("-" * 20 + "\n")
    file.write(original_circuit_text + "\n\n")

    file.write("Transpiled Circuit — Optimization Level 0\n")
    file.write("-" * 20 + "\n")
    file.write(level_0_circuit_text + "\n\n")

    file.write("Transpiled Circuit — Optimization Level 3\n")
    file.write("-" * 20 + "\n")
    file.write(level_3_circuit_text + "\n\n")

    file.write("Circuit Metrics\n")
    file.write("-" * 20 + "\n")
    file.write(f"Optimization level 0 depth: {level_0_depth}\n")
    file.write(f"Optimization level 0 size: {level_0_size}\n")
    file.write(f"Optimization level 0 operations: {dict(level_0_ops)}\n")
    file.write(f"Optimization level 3 depth: {level_3_depth}\n")
    file.write(f"Optimization level 3 size: {level_3_size}\n")
    file.write(f"Optimization level 3 operations: {dict(level_3_ops)}\n\n")

    file.write("Backend\n")
    file.write("-" * 20 + "\n")
    file.write(f"Backend used: {backend.name}\n")
    file.write("Backend type: Simulator\n\n")

    file.write("Measurement Results\n")
    file.write("-" * 20 + "\n")
    file.write(f"Shots: {shots}\n")
    file.write(f"Counts: {counts}\n")
    file.write(f"Correlated outcomes 00 + 11: {correlated}\n")
    file.write(f"Uncorrelated outcomes 01 + 10: {uncorrelated}\n\n")

    file.write("Interpretation\n")
    file.write("-" * 20 + "\n")
    file.write(interpretation + "\n\n")

    file.write("Day 08 Workflow\n")
    file.write("-" * 20 + "\n")
    file.write(
        "Python Program -> Qiskit QuantumCircuit -> Transpiler -> "
        "AerSimulator Backend -> Measurement Counts -> Analysis\n"
    )


print("\nSaved outputs:")
print(f"Counts CSV: {COUNTS_CSV}")
print(f"Layers CSV: {LAYERS_CSV}")
print(f"Report TXT: {REPORT_TXT}")

print("\nDay 08 lab complete.")