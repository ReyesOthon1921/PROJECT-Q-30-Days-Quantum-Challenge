from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import numpy as np
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

zeros = counts.get("0", 0)
ones = counts.get("1", 0)

mean = np.mean([zeros, ones])
std_dev = np.std([zeros, ones])
difference = abs(zeros - ones)

print("Day 07 Statistical Analysis")
print("Zeros:", zeros)
print("Ones:", ones)
print("Mean:", mean)
print("Standard Deviation:", std_dev)
print("Difference between 0 and 1 counts:", difference)

Path("results/csv").mkdir(parents=True, exist_ok=True)

output_file = "results/csv/day07_qrng_statistics.csv"

with open(output_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "project", "metric", "value"])
    writer.writerow(["Day 07", "Quantum Randomness Laboratory", "zeros", zeros])
    writer.writerow(["Day 07", "Quantum Randomness Laboratory", "ones", ones])
    writer.writerow(["Day 07", "Quantum Randomness Laboratory", "mean", mean])
    writer.writerow(["Day 07", "Quantum Randomness Laboratory", "standard_deviation", std_dev])
    writer.writerow(["Day 07", "Quantum Randomness Laboratory", "difference", difference])

print("Saved statistics to:", output_file)
