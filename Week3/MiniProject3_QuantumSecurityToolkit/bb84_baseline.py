"""
Project-Q 30-Day Quantum Computing Challenge
Week 3 Mini Project 3: Quantum Security Toolkit

Checkpoint 1:
BB84 quantum key distribution without an eavesdropper.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator


@dataclass
class BB84Result:
    """Store the results of one BB84 experiment."""

    alice_bits: list[int]
    alice_bases: list[str]
    bob_bases: list[str]
    bob_results: list[int]
    matching_indices: list[int]
    alice_key: list[int]
    bob_key: list[int]
    errors: int
    qber: float


def generate_random_bits(
    amount: int,
    rng: random.Random,
) -> list[int]:
    """Generate random classical bits."""

    return [rng.randint(0, 1) for _ in range(amount)]


def generate_random_bases(
    amount: int,
    rng: random.Random,
) -> list[str]:
    """
    Generate random BB84 bases.

    Z = computational basis
    X = diagonal basis
    """

    return [rng.choice(["Z", "X"]) for _ in range(amount)]


def prepare_alice_state(
    circuit: QuantumCircuit,
    qubit: int,
    bit: int,
    basis: str,
) -> None:
    """
    Prepare one of the four BB84 quantum states.

    Z basis:
        0 -> |0>
        1 -> |1>

    X basis:
        0 -> |+>
        1 -> |->
    """

    if bit == 1:
        circuit.x(qubit)

    if basis == "X":
        circuit.h(qubit)


def add_bob_measurement(
    circuit: QuantumCircuit,
    qubit: int,
    basis: str,
) -> None:
    """Add Bob's selected measurement basis."""

    if basis == "X":
        # Rotate the X basis back into the Z basis before measurement.
        circuit.h(qubit)

    circuit.measure(qubit, qubit)


def build_bb84_circuit(
    alice_bits: list[int],
    alice_bases: list[str],
    bob_bases: list[str],
) -> QuantumCircuit:
    """Build the complete Alice-to-Bob circuit."""

    number_of_qubits = len(alice_bits)

    if not (
        len(alice_bases)
        == len(bob_bases)
        == number_of_qubits
    ):
        raise ValueError("All BB84 input lists must have equal lengths.")

    circuit = QuantumCircuit(
        number_of_qubits,
        number_of_qubits,
        name="BB84_No_Eve",
    )

    # Alice prepares the transmitted quantum states.
    for index in range(number_of_qubits):
        prepare_alice_state(
            circuit=circuit,
            qubit=index,
            bit=alice_bits[index],
            basis=alice_bases[index],
        )

    circuit.barrier(label="Quantum Channel")

    # Bob measures each received qubit.
    for index in range(number_of_qubits):
        add_bob_measurement(
            circuit=circuit,
            qubit=index,
            basis=bob_bases[index],
        )

    return circuit


def simulate_bb84(
    number_of_qubits: int = 16,
    seed: int = 21,
) -> tuple[BB84Result, QuantumCircuit]:
    """Run an ideal BB84 experiment without Eve."""

    if number_of_qubits <= 0:
        raise ValueError("number_of_qubits must be greater than zero.")

    rng = random.Random(seed)

    alice_bits = generate_random_bits(number_of_qubits, rng)
    alice_bases = generate_random_bases(number_of_qubits, rng)
    bob_bases = generate_random_bases(number_of_qubits, rng)

    circuit = build_bb84_circuit(
        alice_bits=alice_bits,
        alice_bases=alice_bases,
        bob_bases=bob_bases,
    )

    simulator = AerSimulator(method="stabilizer")

    compiled_circuit = transpile(
        circuit,
        simulator,
        seed_transpiler=seed,
    )

    job = simulator.run(
        compiled_circuit,
        shots=1,
        memory=True,
        seed_simulator=seed,
    )

    result = job.result()

    measured_string = result.get_memory(compiled_circuit)[0]

    # Qiskit displays classical bits from highest index to lowest.
    # Reverse them so list index i matches qubit index i.
    bob_results = [
        int(bit)
        for bit in measured_string.replace(" ", "")[::-1]
    ]

    matching_indices = [
        index
        for index in range(number_of_qubits)
        if alice_bases[index] == bob_bases[index]
    ]

    alice_key = [
        alice_bits[index]
        for index in matching_indices
    ]

    bob_key = [
        bob_results[index]
        for index in matching_indices
    ]

    errors = sum(
        alice_bit != bob_bit
        for alice_bit, bob_bit in zip(alice_key, bob_key)
    )

    qber = errors / len(alice_key) if alice_key else 0.0

    bb84_result = BB84Result(
        alice_bits=alice_bits,
        alice_bases=alice_bases,
        bob_bases=bob_bases,
        bob_results=bob_results,
        matching_indices=matching_indices,
        alice_key=alice_key,
        bob_key=bob_key,
        errors=errors,
        qber=qber,
    )

    return bb84_result, circuit


def bits_to_text(bits: list[int]) -> str:
    """Convert a list of bits into a readable binary string."""

    return "".join(str(bit) for bit in bits)


def display_results(result: BB84Result) -> None:
    """Print a table explaining the BB84 experiment."""

    matching_positions = set(result.matching_indices)

    print()
    print("=" * 82)
    print("WEEK 3 MINI PROJECT 3 — BB84 BASELINE WITHOUT EVE")
    print("=" * 82)

    print(
        f"{'Index':>5} | "
        f"{'Alice Bit':>9} | "
        f"{'Alice Basis':>11} | "
        f"{'Bob Basis':>9} | "
        f"{'Bob Bit':>7} | "
        f"{'Keep':>5}"
    )

    print("-" * 82)

    for index in range(len(result.alice_bits)):
        keep = "YES" if index in matching_positions else "NO"

        print(
            f"{index:>5} | "
            f"{result.alice_bits[index]:>9} | "
            f"{result.alice_bases[index]:>11} | "
            f"{result.bob_bases[index]:>9} | "
            f"{result.bob_results[index]:>7} | "
            f"{keep:>5}"
        )

    print("-" * 82)
    print(f"Qubits transmitted  : {len(result.alice_bits)}")
    print(f"Matching bases      : {len(result.matching_indices)}")
    print(f"Discarded positions : {len(result.alice_bits) - len(result.matching_indices)}")
    print(f"Alice sifted key    : {bits_to_text(result.alice_key)}")
    print(f"Bob sifted key      : {bits_to_text(result.bob_key)}")
    print(f"Key errors          : {result.errors}")
    print(f"QBER                : {result.qber:.2%}")

    if not result.alice_key:
        print("Security status     : No sifted key was generated.")
    elif result.errors == 0:
        print("Security status     : PASS — Alice and Bob's keys match.")
    else:
        print("Security status     : FAIL — unexpected errors detected.")

    print("=" * 82)


def main() -> None:
    """Run Checkpoint 1."""

    result, circuit = simulate_bb84(
        number_of_qubits=16,
        seed=21,
    )

    display_results(result)

    print()
    print("Qiskit circuit:")
    print(circuit.draw(output="text", fold=120))


if __name__ == "__main__":
    main()