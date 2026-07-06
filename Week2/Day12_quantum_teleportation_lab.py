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

def measure_alice_and_bob(qc):
    """
    q0 = Alice's unknown qubit
    q1 = Alice's half of the Bell pair
    q2 = Bob's half of the Bell pair

    Qiskit prints classical bits from highest index to lowest index.
    To make output look like: Alice_q0 Alice_q1 Bob_check
    we measure:
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
        writer.writerow(["Day 12", lab, experiment, description, outcome, count])

print("Day 12 Lab: Quantum Teleportation")
print("PROJECT-Q 30-Day Quantum Computing Challenge")
print("-" * 60)

# ------------------------------------------------------------
# Lab 1: Create the Bell pair used as the teleportation channel
# Workbook idea:
# Teleportation needs a shared entangled Bell pair.
# Expected pattern: mostly 00 and 11.
# ------------------------------------------------------------

qc_bell = QuantumCircuit(2, 2)
qc_bell.h(0)
qc_bell.cx(0, 1)
qc_bell.measure(0, 1)
qc_bell.measure(1, 0)

counts_bell = run_counts(qc_bell, shots)

print("\nLab 1: Shared Bell Pair")
print(qc_bell.draw(output="text"))
print("Counts:", counts_bell)

# ------------------------------------------------------------
# Lab 2: Teleport the |+> state
# q0 starts as |+>
# q1 and q2 form the Bell pair
# Alice applies CNOT and H
# Bob receives the recovered state after corrections
#
# To verify |+>, we apply H to Bob's qubit before measuring.
# If Bob has |+>, measuring after H should give 0.
# Expected: all final output strings should end in 0.
# ------------------------------------------------------------

qc_teleport_plus = QuantumCircuit(3, 3)

# Prepare Alice's unknown state: |+>
qc_teleport_plus.h(0)

# Create Bell pair between Alice's q1 and Bob's q2
qc_teleport_plus.h(1)
qc_teleport_plus.cx(1, 2)

# Alice's teleportation operations
qc_teleport_plus.cx(0, 1)
qc_teleport_plus.h(0)

# Bob's correction operations using deferred measurement
qc_teleport_plus.cx(1, 2)
qc_teleport_plus.cz(0, 2)

# Verify Bob's qubit is |+> by measuring in the X basis
qc_teleport_plus.h(2)

measure_alice_and_bob(qc_teleport_plus)

counts_plus = run_counts(qc_teleport_plus, shots)

success_plus = sum(count for outcome, count in counts_plus.items() if outcome.endswith("0"))
fail_plus = sum(count for outcome, count in counts_plus.items() if outcome.endswith("1"))

print("\nLab 2: Teleport the |+> State")
print(qc_teleport_plus.draw(output="text"))
print("Counts:", counts_plus)
print("Bob verification success count:", success_plus)
print("Bob verification fail count:", fail_plus)

# ------------------------------------------------------------
# Lab 3: Teleport the |1> state
# q0 starts as |1>
# After teleportation, Bob's qubit should measure as 1.
# Expected: all final output strings should end in 1.
# ------------------------------------------------------------

qc_teleport_one = QuantumCircuit(3, 3)

# Prepare Alice's unknown state: |1>
qc_teleport_one.x(0)

# Create Bell pair
qc_teleport_one.h(1)
qc_teleport_one.cx(1, 2)

# Alice's teleportation operations
qc_teleport_one.cx(0, 1)
qc_teleport_one.h(0)

# Bob's correction operations using deferred measurement
qc_teleport_one.cx(1, 2)
qc_teleport_one.cz(0, 2)

# Verify Bob's qubit directly in the Z basis
measure_alice_and_bob(qc_teleport_one)

counts_one = run_counts(qc_teleport_one, shots)

success_one = sum(count for outcome, count in counts_one.items() if outcome.endswith("1"))
fail_one = sum(count for outcome, count in counts_one.items() if outcome.endswith("0"))

print("\nLab 3: Teleport the |1> State")
print(qc_teleport_one.draw(output="text"))
print("Counts:", counts_one)
print("Bob verification success count:", success_one)
print("Bob verification fail count:", fail_one)

# ------------------------------------------------------------
# Lab 4: Show why Bob's corrections matter
# This repeats teleporting |+>, but skips Bob's corrections.
# Expected: Bob does not always pass the |+> verification.
# ------------------------------------------------------------

qc_no_correction = QuantumCircuit(3, 3)

# Prepare Alice's unknown state: |+>
qc_no_correction.h(0)

# Create Bell pair
qc_no_correction.h(1)
qc_no_correction.cx(1, 2)

# Alice's teleportation operations
qc_no_correction.cx(0, 1)
qc_no_correction.h(0)

# No Bob correction here

# Verify Bob's qubit in the X basis
qc_no_correction.h(2)

measure_alice_and_bob(qc_no_correction)

counts_no_correction = run_counts(qc_no_correction, shots)

success_no_correction = sum(count for outcome, count in counts_no_correction.items() if outcome.endswith("0"))
fail_no_correction = sum(count for outcome, count in counts_no_correction.items() if outcome.endswith("1"))

print("\nLab 4: Teleportation Without Bob's Corrections")
print(qc_no_correction.draw(output="text"))
print("Counts:", counts_no_correction)
print("Bob verification success count:", success_no_correction)
print("Bob verification fail count:", fail_no_correction)

# ------------------------------------------------------------
# Save results
# ------------------------------------------------------------

Path("results/csv").mkdir(parents=True, exist_ok=True)

output_file = "results/csv/day12_quantum_teleportation_lab.csv"

with open(output_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["day", "lab", "experiment", "description", "outcome", "count"])

    save_counts(
        writer,
        "Lab 1",
        "bell_pair_channel",
        "Shared Bell pair used as teleportation channel",
        counts_bell
    )

    save_counts(
        writer,
        "Lab 2",
        "teleport_plus_state",
        "Teleport |+> and verify Bob in X basis",
        counts_plus
    )

    writer.writerow(["Day 12", "Lab 2", "teleport_plus_state_summary", "Bob verification success", "success", success_plus])
    writer.writerow(["Day 12", "Lab 2", "teleport_plus_state_summary", "Bob verification fail", "fail", fail_plus])

    save_counts(
        writer,
        "Lab 3",
        "teleport_one_state",
        "Teleport |1> and verify Bob in Z basis",
        counts_one
    )

    writer.writerow(["Day 12", "Lab 3", "teleport_one_state_summary", "Bob verification success", "success", success_one])
    writer.writerow(["Day 12", "Lab 3", "teleport_one_state_summary", "Bob verification fail", "fail", fail_one])

    save_counts(
        writer,
        "Lab 4",
        "teleport_without_corrections",
        "Shows why Bob's correction gates are necessary",
        counts_no_correction
    )

    writer.writerow(["Day 12", "Lab 4", "teleport_without_corrections_summary", "Bob verification success", "success", success_no_correction])
    writer.writerow(["Day 12", "Lab 4", "teleport_without_corrections_summary", "Bob verification fail", "fail", fail_no_correction])

print("\nSaved lab results to:", output_file)

print("\nLab Summary:")
print("1. Quantum teleportation transfers a quantum state, not a physical particle.")
print("2. The protocol requires an unknown qubit, a shared Bell pair, and classical communication.")
print("3. Alice's operations spread the unknown state across the three-qubit system.")
print("4. Bob's correction gates recover the original state on Bob's qubit.")
print("5. Without Bob's corrections, teleportation does not reliably recover the state.")
