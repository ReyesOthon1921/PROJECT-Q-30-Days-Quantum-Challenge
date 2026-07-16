"""
Automated tests for Week 3 Mini Project 3:
Quantum Security Toolkit.
"""

from __future__ import annotations

import unittest

from bb84_baseline import (
    generate_random_bases,
    generate_random_bits,
    simulate_bb84,
)
from bb84_eve_attack import simulate_eve_attack
from quantum_security_toolkit import (
    create_key_fingerprint,
    security_decision,
)


class TestBB84Baseline(unittest.TestCase):
    """Test BB84 communication without an attacker."""

    def test_random_bit_generation(self) -> None:
        """Generated bits must contain only zero and one."""

        import random

        rng = random.Random(10)
        bits = generate_random_bits(32, rng)

        self.assertEqual(len(bits), 32)
        self.assertTrue(
            all(bit in (0, 1) for bit in bits)
        )

    def test_random_basis_generation(self) -> None:
        """Generated bases must contain only Z and X."""

        import random

        rng = random.Random(10)
        bases = generate_random_bases(32, rng)

        self.assertEqual(len(bases), 32)
        self.assertTrue(
            all(basis in ("Z", "X") for basis in bases)
        )

    def test_secure_channel_has_zero_qber(self) -> None:
        """
        Alice and Bob must produce matching sifted keys
        when Eve is absent.
        """

        result, _ = simulate_bb84(
            number_of_qubits=32,
            seed=21,
        )

        self.assertGreater(
            len(result.alice_key),
            0,
        )

        self.assertEqual(
            result.alice_key,
            result.bob_key,
        )

        self.assertEqual(
            result.errors,
            0,
        )

        self.assertEqual(
            result.qber,
            0.0,
        )


class TestEveAttack(unittest.TestCase):
    """Test the intercept-and-resend attack."""

    def test_eve_introduces_detectable_errors(self) -> None:
        """
        The deterministic 32-qubit experiment should
        produce errors after Eve intercepts every qubit.
        """

        result = simulate_eve_attack(
            number_of_qubits=32,
            seed=25,
        )

        self.assertEqual(
            len(result.alice_bits),
            32,
        )

        self.assertGreater(
            len(result.matching_indices),
            0,
        )

        self.assertGreater(
            result.errors,
            0,
        )

        self.assertGreater(
            result.qber,
            0.11,
        )

        self.assertNotEqual(
            result.alice_key,
            result.bob_key,
        )


class TestSecurityDecision(unittest.TestCase):
    """Test session acceptance and rejection."""

    def test_accepts_qber_below_threshold(self) -> None:
        self.assertEqual(
            security_decision(
                qber=0.0,
                threshold=0.11,
            ),
            "ACCEPTED",
        )

    def test_accepts_qber_equal_to_threshold(self) -> None:
        self.assertEqual(
            security_decision(
                qber=0.11,
                threshold=0.11,
            ),
            "ACCEPTED",
        )

    def test_rejects_qber_above_threshold(self) -> None:
        self.assertEqual(
            security_decision(
                qber=0.25,
                threshold=0.11,
            ),
            "REJECTED",
        )


class TestKeyFingerprint(unittest.TestCase):
    """Test safe sifted-key comparison."""

    def test_same_key_has_same_fingerprint(self) -> None:
        key = [1, 0, 1, 1, 0, 0]

        self.assertEqual(
            create_key_fingerprint(key),
            create_key_fingerprint(key),
        )

    def test_different_keys_have_different_fingerprints(
        self,
    ) -> None:
        first_key = [1, 0, 1, 1]
        second_key = [1, 0, 1, 0]

        self.assertNotEqual(
            create_key_fingerprint(first_key),
            create_key_fingerprint(second_key),
        )

    def test_empty_key_returns_no_key(self) -> None:
        self.assertEqual(
            create_key_fingerprint([]),
            "NO_KEY",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)