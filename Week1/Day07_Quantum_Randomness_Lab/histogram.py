from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
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

print("Day 07 Histogram Results")
print(counts)

Path("results/figures").mkdir(parents=True, exist_ok=True)

figure = plot_histogram(counts, title="Day 07 Quantum Random Bit Distribution")
figure.savefig("results/figures/day07_qrng_histogram.png", bbox_inches="tight")

print("Saved histogram to: results/figures/day07_qrng_histogram.png")
