from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import csv
from pathlib import Path

shots = 1000
simulator = AerSimulator()

print("Day 08 Lab: Understanding Qiskit Architecture")
print("PROJECT-Q 30-Day Quantum Computing Challenge")
print("-" * 70)

# ------------------------------------------------------------
# Layer 1: Python Program
# This is the code we write.
# ------------------------------------------------------------

print("\nLayer 1: Python Program")
print("We write Python code to describe the quantum circuit.")

# ------------------------------------------------------------
# Layer 2: Quantum Circuit / Qiskit SDK
# Qiskit lets us create qubits, gates, measurements, and circuits.
# ------------------------------------------------------------

qc = QuantumCircuit(2, 2)

qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])

print("\nLayer 2: Qiskit SDK and Quantum Circuit")
print(qc.draw(output="text"))

original_depth = qc.depth()
original_size = qc.size()
original_ops = dict(qc.count_ops())

print("Original circuit depth:", original_depth)
print("Original circuit size:", original_size)
print("Original circuit operations:", original_ops)

# ------------------------------------------------------------
# Layer 3: Transpiler
# The transpiler prepares the circuit for a backend.
# ------------------------------------------------------------

compiled_level_0 = transpile(qc, simulator, optimization_level=0)
compiled_level_3 = transpile(qc, simulator, optimization_level=3)

print("\nLayer 3: Transpiler")
print("Transpiled circuit with optimization_level=0:")
print(compiled_level_0.draw(output="text"))

print("Transpiled circuit with optimization_level=3:")
print(compiled_level_3.draw(output="text"))

level_0_depth = compiled_level_0.depth()
level_0_size = compiled_level_0.size()
level_0_ops = dict(compiled_level_0.count_ops())

level_3_depth = compiled_level_3.depth()
level_3_size = compiled_level_3.size()
level_3_ops = dict(compiled_level_3.count_ops())

print("Optimization level 0 depth:", level_0_depth)
print("Optimization level 0 size:", level_0_size)
print("Optimization level 0 operations:", level_0_ops)

print("Optimization level 3 depth:", level_3_depth)
print("Optimization level 3 size:", level_3_size)
print("Optimization level 3 operations:", level_3_ops)

# ------------------------------------------------------------
# Layer 4: Backend
# The backend is where the circuit runs.
# Here we use AerSimulator instead of real IBM Quantum hardware.
# ------------------------------------------------------------

print("\nLayer 4: Backend")
print("Backend used:", simulator.name)
print("Backend type: Simulator")
print("Simulators are useful for learning, debugging, and testing circuits.")

# ------------------------------------------------------------
# Layer 5: Execution and Measurement Results
# The backend executes the circuit and returns measurement counts.
# ------------------------------------------------------------

job = simulator.run(compiled_level_3, shots=shots)
result = job.result()
counts = result.get_counts()

print("\nLayer 5: Measurement Results")
print("Shots:", shots)
print("Counts:", counts)

# ------------------------------------------------------------
# Layer 6: Analysis
# We analyze the measurement result.
# This circuit creates a Bell-style correlation, so ideal results are 00 and 11.
# ------------------------------------------------------------

correlated = counts.get("00", 0) + counts.get("11", 0)
uncorrelated = counts.get("01", 0) + counts.get("10", 0)

print("\nLayer 6: Analysis")
print("Correlated outcomes 00 + 11:", correlated)
print("Uncorrelated outcomes 01 + 10:", uncorrelated)

# ------------------------------------------------------------
# Save CSV outputs
# ------------------------------------------------------------

Path("results/csv").mkdir(parents=True, exist_ok=True)
Path("results/reports").mkdir(parents=True, exist_ok=True)

counts_file = "results/csv/day08_qiskit_architecture_counts.csv"
architecture_file = "results/csv/day08_qiskit_architecture_layers.csv"
report_file = "results/reports/day08_qiskit_architecture_report.txt"

with open(counts_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "lab", "backend", "shots", "outcome", "count"])

    for outcome, count in counts.items():
        writer.writerow(["Day 08", "Qiskit Architecture", simulator.name, shots, outcome, count])

with open(architecture_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "layer", "component", "description"])

    writer.writerow(["Day 08", "Layer 1", "Python Program", "User writes Python code to describe the circuit"])
    writer.writerow(["Day 08", "Layer 2", "Qiskit SDK", "Qiskit creates qubits, gates, circuits, and measurements"])
    writer.writerow(["Day 08", "Layer 3", "Transpiler", "Prepares and optimizes the circuit for the selected backend"])
    writer.writerow(["Day 08", "Layer 4", "Backend", "Simulator or real quantum hardware executes the circuit"])
    writer.writerow(["Day 08", "Layer 5", "Results", "Measurement counts are returned after execution"])
    writer.writerow(["Day 08", "Layer 6", "Analysis", "Counts are interpreted and compared"])

with open(report_file, "w") as file:
    file.write("Day 08 Lab: Understanding Qiskit Architecture\n")
    file.write("PROJECT-Q 30-Day Quantum Computing Challenge\n")
    file.write("=" * 60 + "\n\n")

    file.write("Workflow:\n")
    file.write("Python Program -> Quantum Circuit -> Qiskit SDK -> Transpiler -> Backend -> Results -> Analysis\n\n")

    file.write("Original Circuit:\n")
    file.write(str(qc.draw(output="text")) + "\n\n")

    file.write("Original Circuit Metrics:\n")
    file.write(f"Depth: {original_depth}\n")
    file.write(f"Size: {original_size}\n")
    file.write(f"Operations: {original_ops}\n\n")

    file.write("Transpiled Circuit Metrics:\n")
    file.write(f"Optimization Level 0 Depth: {level_0_depth}\n")
    file.write(f"Optimization Level 0 Size: {level_0_size}\n")
    file.write(f"Optimization Level 0 Operations: {level_0_ops}\n")
    file.write(f"Optimization Level 3 Depth: {level_3_depth}\n")
    file.write(f"Optimization Level 3 Size: {level_3_size}\n")
    file.write(f"Optimization Level 3 Operations: {level_3_ops}\n\n")

    file.write("Backend:\n")
    file.write(f"{simulator.name}\n\n")

    file.write("Measurement Counts:\n")
    file.write(str(counts) + "\n\n")

    file.write("Analysis:\n")
    file.write(f"Correlated outcomes 00 + 11: {correlated}\n")
    file.write(f"Uncorrelated outcomes 01 + 10: {uncorrelated}\n")

print("\nSaved counts to:", counts_file)
print("Saved architecture layers to:", architecture_file)
print("Saved report to:", report_file)

print("\nLab Summary:")
print("1. Python code describes the quantum program.")
print("2. Qiskit builds the quantum circuit.")
print("3. The transpiler prepares the circuit for the backend.")
print("4. The backend executes the circuit.")
print("5. Results return as measurement counts.")
print("6. The results can be analyzed and saved.")
