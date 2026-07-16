"""
Project-Q 30-Day Quantum Computing Challenge
Week 3 Mini Project 3: Quantum Security Toolkit

Checkpoint 3:
Compare secure BB84 communication against Eve's
intercept-and-resend attack across repeated experiments.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev

import matplotlib.pyplot as plt

from bb84_baseline import simulate_bb84
from bb84_eve_attack import simulate_eve_attack


@dataclass(frozen=True)
class SecurityTrial:
    """Store one BB84 security experiment."""

    scenario: str
    trial: int
    seed: int
    qubits_transmitted: int
    sifted_key_length: int
    errors: int
    qber: float
    attack_detected: bool


def validate_inputs(
    trials: int,
    qubits: int,
    threshold: float,
) -> None:
    """Validate command-line experiment settings."""

    if trials <= 0:
        raise ValueError("trials must be greater than zero.")

    if qubits <= 0:
        raise ValueError("qubits must be greater than zero.")

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(
            "threshold must be between 0.0 and 1.0."
        )


def get_output_directories() -> dict[str, Path]:
    """
    Find the repository root and create output folders.

    Current file:
    repository/Week3/MiniProject3_QuantumSecurityToolkit/
        bb84_security_analysis.py
    """

    repository_root = Path(__file__).resolve().parents[2]

    directories = {
        "data": repository_root / "results" / "data",
        "figures": repository_root / "results" / "figures",
        "reports": repository_root / "results" / "reports",
    }

    for directory in directories.values():
        directory.mkdir(parents=True, exist_ok=True)

    return directories


def run_security_trials(
    trials: int,
    qubits: int,
    base_seed: int,
    threshold: float,
) -> list[SecurityTrial]:
    """
    Run repeated experiments with and without Eve.

    Every trial contains:

    1. One ideal BB84 experiment without Eve.
    2. One attacked experiment with Eve.
    """

    records: list[SecurityTrial] = []

    for trial_number in range(1, trials + 1):
        secure_seed = base_seed + trial_number
        attack_seed = base_seed + 100_000 + trial_number

        print(
            f"Running trial {trial_number}/{trials} "
            f"without Eve..."
        )

        secure_result, _ = simulate_bb84(
            number_of_qubits=qubits,
            seed=secure_seed,
        )

        records.append(
            SecurityTrial(
                scenario="No Eve",
                trial=trial_number,
                seed=secure_seed,
                qubits_transmitted=qubits,
                sifted_key_length=len(
                    secure_result.matching_indices
                ),
                errors=secure_result.errors,
                qber=secure_result.qber,
                attack_detected=secure_result.qber > threshold,
            )
        )

        print(
            f"Running trial {trial_number}/{trials} "
            f"with Eve..."
        )

        attack_result = simulate_eve_attack(
            number_of_qubits=qubits,
            seed=attack_seed,
        )

        records.append(
            SecurityTrial(
                scenario="Eve Attack",
                trial=trial_number,
                seed=attack_seed,
                qubits_transmitted=qubits,
                sifted_key_length=len(
                    attack_result.matching_indices
                ),
                errors=attack_result.errors,
                qber=attack_result.qber,
                attack_detected=attack_result.qber > threshold,
            )
        )

    return records


def scenario_records(
    records: list[SecurityTrial],
    scenario: str,
) -> list[SecurityTrial]:
    """Select all records belonging to one scenario."""

    return [
        record
        for record in records
        if record.scenario == scenario
    ]


def save_csv(
    records: list[SecurityTrial],
    destination: Path,
) -> None:
    """Save every experiment to a CSV file."""

    fieldnames = [
        "scenario",
        "trial",
        "seed",
        "qubits_transmitted",
        "sifted_key_length",
        "errors",
        "qber",
        "qber_percent",
        "attack_detected",
    ]

    with destination.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()

        for record in records:
            writer.writerow(
                {
                    "scenario": record.scenario,
                    "trial": record.trial,
                    "seed": record.seed,
                    "qubits_transmitted":
                        record.qubits_transmitted,
                    "sifted_key_length":
                        record.sifted_key_length,
                    "errors": record.errors,
                    "qber": f"{record.qber:.6f}",
                    "qber_percent":
                        f"{record.qber * 100:.2f}",
                    "attack_detected":
                        record.attack_detected,
                }
            )


def create_qber_trial_plot(
    records: list[SecurityTrial],
    threshold: float,
    destination: Path,
) -> None:
    """Plot QBER for every trial."""

    secure = scenario_records(records, "No Eve")
    attacked = scenario_records(records, "Eve Attack")

    figure, axis = plt.subplots(figsize=(10, 6))

    axis.plot(
        [record.trial for record in secure],
        [record.qber * 100 for record in secure],
        marker="o",
        label="No Eve",
    )

    axis.plot(
        [record.trial for record in attacked],
        [record.qber * 100 for record in attacked],
        marker="o",
        label="Eve Attack",
    )

    axis.axhline(
        threshold * 100,
        linestyle="--",
        label=f"Detection Threshold ({threshold:.0%})",
    )

    axis.set_title(
        "BB84 Quantum Bit Error Rate by Trial"
    )
    axis.set_xlabel("Trial")
    axis.set_ylabel("QBER (%)")
    axis.set_ylim(bottom=0)
    axis.grid(True, alpha=0.3)
    axis.legend()

    figure.tight_layout()
    figure.savefig(
        destination,
        dpi=200,
        bbox_inches="tight",
    )
    plt.close(figure)


def create_average_qber_plot(
    records: list[SecurityTrial],
    threshold: float,
    destination: Path,
) -> None:
    """Compare average QBER for secure and attacked channels."""

    secure = scenario_records(records, "No Eve")
    attacked = scenario_records(records, "Eve Attack")

    labels = ["No Eve", "Eve Attack"]

    average_values = [
        mean(record.qber for record in secure) * 100,
        mean(record.qber for record in attacked) * 100,
    ]

    figure, axis = plt.subplots(figsize=(8, 6))

    bars = axis.bar(
        labels,
        average_values,
    )

    axis.axhline(
        threshold * 100,
        linestyle="--",
        label=f"Detection Threshold ({threshold:.0%})",
    )

    axis.set_title(
        "Average BB84 Quantum Bit Error Rate"
    )
    axis.set_ylabel("Average QBER (%)")
    axis.set_ylim(
        0,
        max(
            max(average_values) + 10,
            threshold * 100 + 5,
        ),
    )
    axis.legend()

    for bar, value in zip(bars, average_values):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{value:.2f}%",
            ha="center",
            va="bottom",
        )

    figure.tight_layout()
    figure.savefig(
        destination,
        dpi=200,
        bbox_inches="tight",
    )
    plt.close(figure)


def create_detection_rate_plot(
    records: list[SecurityTrial],
    destination: Path,
) -> None:
    """Display false-alarm and Eve-detection percentages."""

    secure = scenario_records(records, "No Eve")
    attacked = scenario_records(records, "Eve Attack")

    false_alarm_rate = (
        sum(record.attack_detected for record in secure)
        / len(secure)
        * 100
    )

    attack_detection_rate = (
        sum(record.attack_detected for record in attacked)
        / len(attacked)
        * 100
    )

    labels = [
        "False Alarms\n(No Eve)",
        "Attacks Detected\n(Eve Present)",
    ]

    values = [
        false_alarm_rate,
        attack_detection_rate,
    ]

    figure, axis = plt.subplots(figsize=(8, 6))

    bars = axis.bar(labels, values)

    axis.set_title(
        "BB84 Security Detection Performance"
    )
    axis.set_ylabel("Detection Rate (%)")
    axis.set_ylim(0, 110)

    for bar, value in zip(bars, values):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 2,
            f"{value:.1f}%",
            ha="center",
            va="bottom",
        )

    figure.tight_layout()
    figure.savefig(
        destination,
        dpi=200,
        bbox_inches="tight",
    )
    plt.close(figure)


def build_summary(
    records: list[SecurityTrial],
    threshold: float,
    trials: int,
    qubits: int,
) -> str:
    """Build the checkpoint report."""

    secure = scenario_records(records, "No Eve")
    attacked = scenario_records(records, "Eve Attack")

    secure_qbers = [
        record.qber
        for record in secure
    ]

    attacked_qbers = [
        record.qber
        for record in attacked
    ]

    secure_sifted_lengths = [
        record.sifted_key_length
        for record in secure
    ]

    attacked_sifted_lengths = [
        record.sifted_key_length
        for record in attacked
    ]

    false_alarms = sum(
        record.attack_detected
        for record in secure
    )

    attacks_detected = sum(
        record.attack_detected
        for record in attacked
    )

    false_alarm_rate = false_alarms / trials
    attack_detection_rate = attacks_detected / trials

    lines = [
        "PROJECT-Q 30-DAY QUANTUM COMPUTING CHALLENGE",
        "WEEK 3 MINI PROJECT 3 — QUANTUM SECURITY TOOLKIT",
        "CHECKPOINT 3: SECURITY ANALYSIS",
        "",
        "EXPERIMENT CONFIGURATION",
        f"Trials per scenario       : {trials}",
        f"Qubits per trial          : {qubits}",
        f"Detection threshold       : {threshold:.2%}",
        "",
        "NO-EVE CHANNEL",
        (
            "Average QBER             : "
            f"{mean(secure_qbers):.2%}"
        ),
        (
            "QBER standard deviation  : "
            f"{pstdev(secure_qbers):.2%}"
        ),
        (
            "Average sifted key length: "
            f"{mean(secure_sifted_lengths):.2f}"
        ),
        f"False alarms              : {false_alarms}",
        (
            "False-alarm rate         : "
            f"{false_alarm_rate:.2%}"
        ),
        "",
        "EVE INTERCEPT-AND-RESEND CHANNEL",
        (
            "Average QBER             : "
            f"{mean(attacked_qbers):.2%}"
        ),
        (
            "QBER standard deviation  : "
            f"{pstdev(attacked_qbers):.2%}"
        ),
        (
            "Average sifted key length: "
            f"{mean(attacked_sifted_lengths):.2f}"
        ),
        f"Attacks detected          : {attacks_detected}",
        (
            "Attack detection rate    : "
            f"{attack_detection_rate:.2%}"
        ),
        "",
        "INTERPRETATION",
        (
            "The ideal channel should produce matching sifted "
            "keys and approximately 0% QBER."
        ),
        (
            "An intercept-and-resend attack should produce an "
            "average QBER near 25% because Eve guesses the "
            "wrong basis approximately half the time, and half "
            "of those disturbed states produce incorrect bits."
        ),
        (
            "A QBER above the educational detection threshold "
            "causes the session to be rejected."
        ),
        "",
        "NOTE",
        (
            "This threshold is used for an educational simulation. "
            "Real QKD deployments require device characterization, "
            "authenticated classical communication, error "
            "correction, privacy amplification, and a complete "
            "security proof."
        ),
    ]

    return "\n".join(lines)


def save_report(
    summary: str,
    destination: Path,
) -> None:
    """Save the text report."""

    destination.write_text(
        summary,
        encoding="utf-8",
    )


def display_terminal_summary(
    summary: str,
    output_files: list[Path],
) -> None:
    """Print the results and saved file locations."""

    print()
    print("=" * 78)
    print(summary)
    print("=" * 78)
    print()
    print("Saved output files:")

    for output_file in output_files:
        print(f"  {output_file}")


def parse_arguments() -> argparse.Namespace:
    """Read experiment settings from the command line."""

    parser = argparse.ArgumentParser(
        description=(
            "Compare normal BB84 communication against "
            "Eve's intercept-and-resend attack."
        )
    )

    parser.add_argument(
        "--trials",
        type=int,
        default=10,
        help="Number of experiments per scenario. Default: 10",
    )

    parser.add_argument(
        "--qubits",
        type=int,
        default=64,
        help="Number of qubits per experiment. Default: 64",
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.11,
        help=(
            "Educational QBER detection threshold as a decimal. "
            "Default: 0.11"
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=300,
        help="Base random seed. Default: 300",
    )

    return parser.parse_args()


def main() -> None:
    """Run the complete security comparison."""

    arguments = parse_arguments()

    validate_inputs(
        trials=arguments.trials,
        qubits=arguments.qubits,
        threshold=arguments.threshold,
    )

    directories = get_output_directories()

    csv_path = (
        directories["data"]
        / "miniproject3_security_trials.csv"
    )

    qber_trial_plot_path = (
        directories["figures"]
        / "miniproject3_qber_by_trial.png"
    )

    average_qber_plot_path = (
        directories["figures"]
        / "miniproject3_average_qber.png"
    )

    detection_plot_path = (
        directories["figures"]
        / "miniproject3_detection_rate.png"
    )

    report_path = (
        directories["reports"]
        / "miniproject3_security_analysis.txt"
    )

    records = run_security_trials(
        trials=arguments.trials,
        qubits=arguments.qubits,
        base_seed=arguments.seed,
        threshold=arguments.threshold,
    )

    save_csv(records, csv_path)

    create_qber_trial_plot(
        records=records,
        threshold=arguments.threshold,
        destination=qber_trial_plot_path,
    )

    create_average_qber_plot(
        records=records,
        threshold=arguments.threshold,
        destination=average_qber_plot_path,
    )

    create_detection_rate_plot(
        records=records,
        destination=detection_plot_path,
    )

    summary = build_summary(
        records=records,
        threshold=arguments.threshold,
        trials=arguments.trials,
        qubits=arguments.qubits,
    )

    save_report(summary, report_path)

    display_terminal_summary(
        summary=summary,
        output_files=[
            csv_path,
            qber_trial_plot_path,
            average_qber_plot_path,
            detection_plot_path,
            report_path,
        ],
    )


if __name__ == "__main__":
    main()