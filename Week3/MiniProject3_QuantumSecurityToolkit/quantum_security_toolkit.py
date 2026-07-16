"""
Project-Q 30-Day Quantum Computing Challenge
Week 3 Mini Project 3: Quantum Security Toolkit

Checkpoint 4:
Unified BB84 security demonstration.

This program compares:

1. An ideal BB84 channel without Eve.
2. A BB84 channel under an intercept-and-resend attack.

It then applies an educational QBER threshold and saves
a final JSON record and text report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from bb84_baseline import simulate_bb84
from bb84_eve_attack import simulate_eve_attack


def validate_inputs(
    qubits: int,
    threshold: float,
) -> None:
    """Validate toolkit settings."""

    if qubits <= 0:
        raise ValueError("qubits must be greater than zero.")

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(
            "threshold must be between 0.0 and 1.0."
        )


def bits_to_string(bits: list[int]) -> str:
    """Convert a list of bits into a binary string."""

    return "".join(str(bit) for bit in bits)


def create_key_fingerprint(bits: list[int]) -> str:
    """
    Create a short SHA-256 fingerprint of a sifted key.

    The fingerprint lets us compare keys without printing
    the complete secret key in the final report.
    """

    if not bits:
        return "NO_KEY"

    binary_key = bits_to_string(bits)

    digest = hashlib.sha256(
        binary_key.encode("utf-8")
    ).hexdigest()

    return digest[:16]


def security_decision(
    qber: float,
    threshold: float,
) -> str:
    """Accept or reject a communication session."""

    if qber > threshold:
        return "REJECTED"

    return "ACCEPTED"


def get_output_directories() -> dict[str, Path]:
    """Create and return repository output directories."""

    repository_root = Path(__file__).resolve().parents[2]

    directories = {
        "data": repository_root / "results" / "data",
        "reports": repository_root / "results" / "reports",
    }

    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)

    return directories


def build_secure_channel_record(
    qubits: int,
    seed: int,
    threshold: float,
) -> dict[str, Any]:
    """Run and describe a BB84 session without Eve."""

    result, _ = simulate_bb84(
        number_of_qubits=qubits,
        seed=seed,
    )

    alice_fingerprint = create_key_fingerprint(
        result.alice_key
    )

    bob_fingerprint = create_key_fingerprint(
        result.bob_key
    )

    return {
        "scenario": "Secure BB84 channel without Eve",
        "seed": seed,
        "qubits_transmitted": qubits,
        "matching_bases": len(result.matching_indices),
        "discarded_positions": (
            qubits - len(result.matching_indices)
        ),
        "sifted_key_length": len(result.alice_key),
        "errors": result.errors,
        "qber": result.qber,
        "qber_percent": result.qber * 100,
        "detection_threshold": threshold,
        "session_decision": security_decision(
            result.qber,
            threshold,
        ),
        "alice_key_fingerprint": alice_fingerprint,
        "bob_key_fingerprint": bob_fingerprint,
        "key_fingerprints_match": (
            alice_fingerprint == bob_fingerprint
        ),
    }


def build_attacked_channel_record(
    qubits: int,
    seed: int,
    threshold: float,
) -> dict[str, Any]:
    """Run and describe BB84 under Eve's attack."""

    result = simulate_eve_attack(
        number_of_qubits=qubits,
        seed=seed,
    )

    alice_fingerprint = create_key_fingerprint(
        result.alice_key
    )

    bob_fingerprint = create_key_fingerprint(
        result.bob_key
    )

    eve_basis_matches = sum(
        alice_basis == eve_basis
        for alice_basis, eve_basis in zip(
            result.alice_bases,
            result.eve_bases,
        )
    )

    return {
        "scenario": "BB84 intercept-and-resend attack",
        "seed": seed,
        "qubits_transmitted": qubits,
        "qubits_intercepted_by_eve": qubits,
        "eve_alice_basis_matches": eve_basis_matches,
        "matching_bases": len(result.matching_indices),
        "discarded_positions": (
            qubits - len(result.matching_indices)
        ),
        "sifted_key_length": len(result.alice_key),
        "error_positions": result.error_indices,
        "errors": result.errors,
        "qber": result.qber,
        "qber_percent": result.qber * 100,
        "detection_threshold": threshold,
        "session_decision": security_decision(
            result.qber,
            threshold,
        ),
        "eavesdropper_detected": (
            result.qber > threshold
        ),
        "alice_key_fingerprint": alice_fingerprint,
        "bob_key_fingerprint": bob_fingerprint,
        "key_fingerprints_match": (
            alice_fingerprint == bob_fingerprint
        ),
    }


def build_final_results(
    qubits: int,
    seed: int,
    threshold: float,
) -> dict[str, Any]:
    """Run both scenarios and create the final result bundle."""

    secure_channel = build_secure_channel_record(
        qubits=qubits,
        seed=seed,
        threshold=threshold,
    )

    attacked_channel = build_attacked_channel_record(
        qubits=qubits,
        seed=seed + 100_000,
        threshold=threshold,
    )

    secure_qber = float(secure_channel["qber"])
    attacked_qber = float(attacked_channel["qber"])

    secure_passed = (
        secure_channel["session_decision"] == "ACCEPTED"
        and secure_channel["key_fingerprints_match"]
    )

    attack_detected = bool(
        attacked_channel["eavesdropper_detected"]
    )

    toolkit_passed = secure_passed and attack_detected

    return {
        "project": (
            "Project-Q 30-Day Quantum Computing Challenge"
        ),
        "mini_project": (
            "Week 3 Mini Project 3: "
            "Quantum Security Toolkit"
        ),
        "experiment_configuration": {
            "qubits_per_scenario": qubits,
            "base_seed": seed,
            "educational_qber_threshold": threshold,
            "simulator_method": "stabilizer",
        },
        "secure_channel": secure_channel,
        "attacked_channel": attacked_channel,
        "comparison": {
            "secure_channel_qber_percent":
                secure_qber * 100,
            "attacked_channel_qber_percent":
                attacked_qber * 100,
            "qber_increase_percentage_points":
                (attacked_qber - secure_qber) * 100,
            "secure_channel_passed": secure_passed,
            "attack_detected": attack_detected,
        },
        "final_validation": {
            "toolkit_passed": toolkit_passed,
            "status": (
                "PASS"
                if toolkit_passed
                else "REVIEW_REQUIRED"
            ),
            "conclusion": (
                "The ideal BB84 channel generated matching "
                "sifted keys, while Eve's intercept-and-resend "
                "attack introduced a detectable increase in QBER."
                if toolkit_passed
                else
                "One or more expected security checks did not "
                "pass. Review the experiment results."
            ),
        },
        "limitations": [
            (
                "This is an educational simulation rather than "
                "a production quantum communication system."
            ),
            (
                "The classical communication channel is assumed "
                "to be authenticated."
            ),
            (
                "Error correction and privacy amplification are "
                "not implemented."
            ),
            (
                "The QBER threshold is an educational experiment "
                "setting and not a complete security proof."
            ),
        ],
    }


def build_text_report(
    final_results: dict[str, Any],
) -> str:
    """Convert the final result bundle into a text report."""

    configuration = final_results[
        "experiment_configuration"
    ]

    secure = final_results["secure_channel"]
    attacked = final_results["attacked_channel"]
    comparison = final_results["comparison"]
    validation = final_results["final_validation"]

    lines = [
        "=" * 78,
        "PROJECT-Q 30-DAY QUANTUM COMPUTING CHALLENGE",
        "WEEK 3 MINI PROJECT 3 — QUANTUM SECURITY TOOLKIT",
        "CHECKPOINT 4: UNIFIED FINAL DEMONSTRATION",
        "=" * 78,
        "",
        "EXPERIMENT CONFIGURATION",
        (
            "Qubits per scenario       : "
            f"{configuration['qubits_per_scenario']}"
        ),
        (
            "Base seed                 : "
            f"{configuration['base_seed']}"
        ),
        (
            "Educational QBER threshold: "
            f"{configuration['educational_qber_threshold']:.2%}"
        ),
        (
            "Simulator method          : "
            f"{configuration['simulator_method']}"
        ),
        "",
        "SECURE BB84 CHANNEL",
        (
            "Qubits transmitted        : "
            f"{secure['qubits_transmitted']}"
        ),
        (
            "Matching bases            : "
            f"{secure['matching_bases']}"
        ),
        (
            "Sifted key length         : "
            f"{secure['sifted_key_length']}"
        ),
        (
            "Key errors                : "
            f"{secure['errors']}"
        ),
        (
            "QBER                      : "
            f"{secure['qber_percent']:.2f}%"
        ),
        (
            "Key fingerprints match    : "
            f"{secure['key_fingerprints_match']}"
        ),
        (
            "Session decision          : "
            f"{secure['session_decision']}"
        ),
        "",
        "EVE INTERCEPT-AND-RESEND CHANNEL",
        (
            "Qubits intercepted        : "
            f"{attacked['qubits_intercepted_by_eve']}"
        ),
        (
            "Eve/Alice basis matches   : "
            f"{attacked['eve_alice_basis_matches']}"
        ),
        (
            "Alice/Bob matching bases  : "
            f"{attacked['matching_bases']}"
        ),
        (
            "Sifted key length         : "
            f"{attacked['sifted_key_length']}"
        ),
        (
            "Key errors                : "
            f"{attacked['errors']}"
        ),
        (
            "QBER                      : "
            f"{attacked['qber_percent']:.2f}%"
        ),
        (
            "Key fingerprints match    : "
            f"{attacked['key_fingerprints_match']}"
        ),
        (
            "Eavesdropper detected     : "
            f"{attacked['eavesdropper_detected']}"
        ),
        (
            "Session decision          : "
            f"{attacked['session_decision']}"
        ),
        "",
        "SECURITY COMPARISON",
        (
            "Secure-channel QBER       : "
            f"{comparison['secure_channel_qber_percent']:.2f}%"
        ),
        (
            "Attacked-channel QBER     : "
            f"{comparison['attacked_channel_qber_percent']:.2f}%"
        ),
        (
            "QBER increase             : "
            f"{comparison['qber_increase_percentage_points']:.2f} "
            "percentage points"
        ),
        "",
        "FINAL VALIDATION",
        (
            "Toolkit status            : "
            f"{validation['status']}"
        ),
        validation["conclusion"],
        "",
        "LIMITATIONS",
    ]

    for limitation in final_results["limitations"]:
        lines.append(f"- {limitation}")

    lines.append("")
    lines.append("=" * 78)

    return "\n".join(lines)


def save_results(
    final_results: dict[str, Any],
    report: str,
    directories: dict[str, Path],
) -> tuple[Path, Path]:
    """Save JSON and text outputs."""

    json_path = (
        directories["data"]
        / "miniproject3_final_demo.json"
    )

    report_path = (
        directories["reports"]
        / "miniproject3_final_demo.txt"
    )

    json_path.write_text(
        json.dumps(
            final_results,
            indent=2,
        ),
        encoding="utf-8",
    )

    report_path.write_text(
        report,
        encoding="utf-8",
    )

    return json_path, report_path


def parse_arguments() -> argparse.Namespace:
    """Read command-line settings."""

    parser = argparse.ArgumentParser(
        description=(
            "Run the unified Project-Q BB84 "
            "Quantum Security Toolkit."
        )
    )

    parser.add_argument(
        "--qubits",
        type=int,
        default=128,
        help=(
            "Number of qubits in each scenario. "
            "Default: 128"
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=700,
        help="Base experiment seed. Default: 700",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.11,
        help=(
            "Educational QBER threshold as a decimal. "
            "Default: 0.11"
        ),
    )

    return parser.parse_args()


def main() -> None:
    """Run the integrated toolkit demonstration."""

    arguments = parse_arguments()

    validate_inputs(
        qubits=arguments.qubits,
        threshold=arguments.threshold,
    )

    print(
        "Running secure BB84 channel "
        f"with {arguments.qubits} qubits..."
    )

    print(
        "Running Eve intercept-and-resend channel "
        f"with {arguments.qubits} qubits..."
    )

    final_results = build_final_results(
        qubits=arguments.qubits,
        seed=arguments.seed,
        threshold=arguments.threshold,
    )

    report = build_text_report(final_results)

    directories = get_output_directories()

    json_path, report_path = save_results(
        final_results=final_results,
        report=report,
        directories=directories,
    )

    print()
    print(report)
    print()
    print("Saved output files:")
    print(f"  {json_path}")
    print(f"  {report_path}")


if __name__ == "__main__":
    main()