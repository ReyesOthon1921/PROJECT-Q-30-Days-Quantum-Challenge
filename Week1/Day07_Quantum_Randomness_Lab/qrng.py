from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import csv
from pathlib import Path

shots = 1000
simulator = AerSimulator()

qc = QuantumCircuit(1, 1)
qc.h(0)
qc.measure(0, 0)

compiled = transpile(qc, simulator)
job = simulator.run(compiled, shots=shots)
result = job.result()
counts = result.get_counts()

print("Day 07 Mini Project: Quantum Randomness Laboratory")
print("Quantum Random Numbers")
print(counts)

Path("results/csv").mkdir(parents=True, exist_ok=True)

output_file = "results/csv/day07_qrng_counts.csv"

with open(output_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "project", "experiment", "outcome", "count"])

    for outcome, count in counts.items():
        writer.writerow(["Day 07", "Quantum Randomness Laboratory", "qrng_hadamard_measurement", outcome, count])

print("Saved results to:", output_file)
