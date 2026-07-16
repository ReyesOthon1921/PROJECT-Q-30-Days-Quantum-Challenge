"""
Project-Q 30-Day Quantum Computing Challenge
Week 3 Mini Project 3: Quantum Security Toolkit

Checkpoint 2:
Simulate Eve's intercept-and-resend attack against BB84.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from bb84_baseline import (
    bits_to_text,
    generate_random_bases,
    generate_random_bits,
    prepare_alice_state,
)


@dataclass
class EveAttackResult:
    """Store the results of one BB84 intercept-and-resend attack."""

    alice_bits: list[int]
    alice_bases: list[str]

    eve_bases: list[str]
    eve_results: list[int]

    bob_bases: list[str]
    bob_results: list[int]

    matching_indices: list[int]
    error_indices: list[int]

    alice_key: list[int]
    bob_key: list[int]

    errors: int
    qber: float


def measure_bb84_state(
    state_bit: int,
    state_basis: str,
    measurement_basis: str,
    simulator: AerSimulator,
    seed: int,
) -> int:
    """
    Prepare one BB84 state and measure it in a selected basis.

    This function is used twice:

    1. Eve measures the state prepared by Alice.
    2. Bob measures the replacement state prepared by Eve.
    """

    circuit = QuantumCircuit(1, 1)

    # Prepare the input state.
    prepare_alice_state(
        circuit=circuit,
        qubit=0,
        bit=state_bit,
        basis=state_basis,
    )

    circuit.barrier()

    # Measuring in the X basis requires an H rotation first.
    if measurement_basis == "X":
        circuit.h(0)

    circuit.measure(0, 0)

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

    return int(measured_string.replace(" ", "")[-1])


def simulate_eve_attack(
    number_of_qubits: int = 32,
    seed: int = 25,
) -> EveAttackResult:
    """
    Run BB84 with Eve performing an intercept-and-resend attack.

    Eve intercepts every transmitted qubit.
    """

    if number_of_qubits <= 0:
        raise ValueError("number_of_qubits must be greater than zero.")

    rng = random.Random(seed)
    simulator = AerSimulator(method="stabilizer")

    # Alice's private information.
    alice_bits = generate_random_bits(number_of_qubits, rng)
    alice_bases = generate_random_bases(number_of_qubits, rng)

    # Bob independently chooses his measurement bases.
    bob_bases = generate_random_bases(number_of_qubits, rng)

    # Eve does not know Alice's bases and must guess.
    eve_bases = generate_random_bases(number_of_qubits, rng)

    eve_results: list[int] = []
    bob_results: list[int] = []

    for index in range(number_of_qubits):
        # Stage 1:
        # Eve intercepts Alice's qubit and measures it.
        eve_bit = measure_bb84_state(
            state_bit=alice_bits[index],
            state_basis=alice_bases[index],
            measurement_basis=eve_bases[index],
            simulator=simulator,
            seed=seed + 1000 + index,
        )

        eve_results.append(eve_bit)

        # Stage 2:
        # Eve prepares a new qubit using her measured bit and basis.
        # Bob receives and measures this replacement qubit.
        bob_bit = measure_bb84_state(
            state_bit=eve_bit,
            state_basis=eve_bases[index],
            measurement_basis=bob_bases[index],
            simulator=simulator,
            seed=seed + 2000 + index,
        )

        bob_results.append(bob_bit)

    # Alice and Bob publicly compare only their basis choices.
    matching_indices = [
        index
        for index in range(number_of_qubits)
        if alice_bases[index] == bob_bases[index]
    ]

    # They keep only positions where their bases matched.
    alice_key = [
        alice_bits[index]
        for index in matching_indices
    ]

    bob_key = [
        bob_results[index]
        for index in matching_indices
    ]

    # Find errors in the sifted key.
    error_indices = [
        index
        for index in matching_indices
        if alice_bits[index] != bob_results[index]
    ]

    errors = len(error_indices)
    qber = errors / len(matching_indices) if matching_indices else 0.0

    return EveAttackResult(
        alice_bits=alice_bits,
        alice_bases=alice_bases,
        eve_bases=eve_bases,
        eve_results=eve_results,
        bob_bases=bob_bases,
        bob_results=bob_results,
        matching_indices=matching_indices,
        error_indices=error_indices,
        alice_key=alice_key,
        bob_key=bob_key,
        errors=errors,
        qber=qber,
    )


def display_attack_results(result: EveAttackResult) -> None:
    """Print a detailed table explaining Eve's attack."""

    matching_positions = set(result.matching_indices)
    error_positions = set(result.error_indices)

    print()
    print("=" * 112)
    print("WEEK 3 MINI PROJECT 3 — EVE INTERCEPT-AND-RESEND ATTACK")
    print("=" * 112)

    print(
        f"{'Index':>5} | "
        f"{'A Bit':>5} | "
        f"{'A Basis':>7} | "
        f"{'E Basis':>7} | "
        f"{'E Bit':>5} | "
        f"{'B Basis':>7} | "
        f"{'B Bit':>5} | "
        f"{'Keep':>5} | "
        f"{'Error':>5}"
    )

    print("-" * 112)

    for index in range(len(result.alice_bits)):
        keep = "YES" if index in matching_positions else "NO"

        if index not in matching_positions:
            error = "-"
        elif index in error_positions:
            error = "YES"
        else:
            error = "NO"

        print(
            f"{index:>5} | "
            f"{result.alice_bits[index]:>5} | "
            f"{result.alice_bases[index]:>7} | "
            f"{result.eve_bases[index]:>7} | "
            f"{result.eve_results[index]:>5} | "
            f"{result.bob_bases[index]:>7} | "
            f"{result.bob_results[index]:>5} | "
            f"{keep:>5} | "
            f"{error:>5}"
        )

    eve_basis_matches = sum(
        alice_basis == eve_basis
        for alice_basis, eve_basis in zip(
            result.alice_bases,
            result.eve_bases,
        )
    )

    print("-" * 112)
    print(f"Qubits transmitted       : {len(result.alice_bits)}")
    print(f"Eve intercepted          : {len(result.alice_bits)}")
    print(f"Eve matched Alice's basis: {eve_basis_matches}")
    print(f"Alice/Bob matching bases : {len(result.matching_indices)}")
    print(
        "Discarded positions     : "
        f"{len(result.alice_bits) - len(result.matching_indices)}"
    )
    print(f"Alice sifted key         : {bits_to_text(result.alice_key)}")
    print(f"Bob sifted key           : {bits_to_text(result.bob_key)}")
    print(f"Error positions          : {result.error_indices}")
    print(f"Key errors               : {result.errors}")
    print(f"QBER                     : {result.qber:.2%}")

    if not result.alice_key:
        print("Attack result             : No sifted key was generated.")
    elif result.errors > 0:
        print(
            "Attack result             : Eve introduced detectable "
            "measurement errors."
        )
    else:
        print(
            "Attack result             : No error appeared in this small "
            "sample. A larger trial is required."
        )

    print("=" * 112)


def main() -> None:
    """Run the intercept-and-resend experiment."""

    result = simulate_eve_attack(
        number_of_qubits=32,
        seed=25,
    )

    display_attack_results(result)


if __name__ == "__main__":
    main()