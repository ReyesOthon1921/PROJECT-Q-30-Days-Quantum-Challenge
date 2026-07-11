from __future__ import annotations

import math
import time
from pathlib import Path
from typing import List, Tuple

import numpy as np
import matplotlib.pyplot as plt

from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp


ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "results" / "reports"
FIGURE_DIR = ROOT / "results" / "figures"

REPORT_DIR.mkdir(parents=True, exist_ok=True)
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

REPORT_PATH = REPORT_DIR / "day16_qml_report.txt"
LOSS_FIGURE_PATH = FIGURE_DIR / "day16_loss_curve.png"
CIRCUIT_FIGURE_PATH = FIGURE_DIR / "day16_qml_circuit.png"

RANDOM_SEED = 16
TRAINING_STEPS = 90


def create_training_data() -> Tuple[np.ndarray, np.ndarray]:
    """
    Small beginner-friendly dataset.

    Class -1 represents one group.
    Class +1 represents another group.

    The numbers are already treated as angle-style features for a small
    2-qubit quantum feature map.
    """

    features = np.array(
        [
            [0.20, 0.15],
            [0.35, 0.25],
            [0.25, 0.40],
            [2.40, 2.65],
            [2.70, 2.50],
            [2.85, 2.90],
        ],
        dtype=float,
    )

    labels = np.array([-1, -1, -1, 1, 1, 1], dtype=float)

    return features, labels


def build_qml_circuit(features: np.ndarray, parameters: np.ndarray) -> QuantumCircuit:
    """
    Build a simple QML-style circuit.

    Part 1: quantum data encoding
    Part 2: trainable parameterized quantum circuit
    """

    circuit = QuantumCircuit(2)

    x0 = float(features[0])
    x1 = float(features[1])

    theta0 = float(parameters[0])
    theta1 = float(parameters[1])
    theta2 = float(parameters[2])
    theta3 = float(parameters[3])

    # Quantum data encoding / feature map
    circuit.ry(x0, 0)
    circuit.ry(x1, 1)
    circuit.rz(x0 * x1, 0)
    circuit.cx(0, 1)

    # Parameterized trainable circuit / ansatz
    circuit.ry(theta0, 0)
    circuit.ry(theta1, 1)
    circuit.cx(0, 1)
    circuit.rz(theta2, 0)
    circuit.ry(theta3, 1)

    return circuit


def expectation_value(features: np.ndarray, parameters: np.ndarray) -> float:
    """
    Measure the expectation value of Z on qubit 0.

    The expectation value becomes the model's numerical prediction.
    """

    circuit = build_qml_circuit(features, parameters)
    state = Statevector.from_instruction(circuit)

    observable = SparsePauliOp.from_list([("IZ", 1.0)])
    value = state.expectation_value(observable)

    return float(np.real(value))


def predict_label(features: np.ndarray, parameters: np.ndarray) -> int:
    prediction_value = expectation_value(features, parameters)
    return 1 if prediction_value >= 0 else -1


def loss_function(data: np.ndarray, labels: np.ndarray, parameters: np.ndarray) -> float:
    """
    Mean squared error loss.

    Smaller loss means the model predictions are closer to the correct labels.
    """

    predictions = np.array(
        [expectation_value(sample, parameters) for sample in data],
        dtype=float,
    )

    loss = np.mean((labels - predictions) ** 2)

    return float(loss)


def train_parameters(data: np.ndarray, labels: np.ndarray) -> Tuple[np.ndarray, List[float]]:
    """
    Simple classical optimizer.

    This is not a production optimizer. It is a beginner-friendly demonstration
    of the hybrid QML idea: update parameters, rerun the circuit, reduce loss.
    """

    rng = np.random.default_rng(RANDOM_SEED)

    parameters = rng.uniform(-math.pi, math.pi, size=4)
    best_loss = loss_function(data, labels, parameters)

    loss_history = [best_loss]
    step_size = 0.75

    for _ in range(TRAINING_STEPS):
        candidate = parameters + rng.normal(0.0, step_size, size=4)
        candidate_loss = loss_function(data, labels, candidate)

        if candidate_loss < best_loss:
            parameters = candidate
            best_loss = candidate_loss

        loss_history.append(best_loss)
        step_size *= 0.97

    return parameters, loss_history


def make_loss_plot(loss_history: List[float]) -> None:
    plt.figure(figsize=(8, 5))
    plt.plot(range(len(loss_history)), loss_history, marker="o")
    plt.title("Day 16 QML Training Loss")
    plt.xlabel("Optimization Step")
    plt.ylabel("Mean Squared Error Loss")
    plt.tight_layout()
    plt.savefig(LOSS_FIGURE_PATH, dpi=200)
    plt.close()


def make_circuit_figure(features: np.ndarray, parameters: np.ndarray) -> None:
    circuit = build_qml_circuit(features, parameters)

    try:
        drawing = circuit.draw(output="mpl")
        drawing.savefig(CIRCUIT_FIGURE_PATH, dpi=200, bbox_inches="tight")
        plt.close()
    except Exception:
        fallback_path = CIRCUIT_FIGURE_PATH.with_suffix(".txt")
        fallback_path.write_text(str(circuit.draw(output="text")), encoding="utf-8")


def write_report(
    data: np.ndarray,
    labels: np.ndarray,
    parameters: np.ndarray,
    loss_history: List[float],
) -> None:
    initial_loss = loss_history[0]
    final_loss = loss_history[-1]

    rows = []

    correct = 0

    for index, sample in enumerate(data):
        expected = int(labels[index])
        raw_value = expectation_value(sample, parameters)
        predicted = predict_label(sample, parameters)

        if predicted == expected:
            correct += 1

        rows.append(
            {
                "sample": index + 1,
                "features": sample.tolist(),
                "expected": expected,
                "raw_expectation": round(raw_value, 6),
                "predicted": predicted,
                "correct": predicted == expected,
            }
        )

    accuracy = correct / len(data)

    lines = [
        "PROJECT-Q 30-Day Quantum Computing Challenge",
        "Day 16 — Quantum Machine Learning Lab",
        "",
        "Purpose",
        "This lab demonstrates the core idea of Quantum Machine Learning using a small",
        "hybrid quantum-classical workflow.",
        "",
        "Workflow",
        "1. Start with a small classical dataset.",
        "2. Encode classical features into qubit rotations.",
        "3. Process the encoded data with a parameterized quantum circuit.",
        "4. Measure an expectation value from the quantum state.",
        "5. Compare the output with the correct label using a loss function.",
        "6. Use a classical optimizer loop to update circuit parameters.",
        "",
        "Important Note",
        "This lab is a beginner QML demonstration. It does not claim quantum advantage.",
        "",
        "Training Summary",
        f"Training samples: {len(data)}",
        f"Trainable parameters: {len(parameters)}",
        f"Training steps: {TRAINING_STEPS}",
        f"Initial loss: {initial_loss:.6f}",
        f"Final loss: {final_loss:.6f}",
        f"Accuracy on small demo dataset: {accuracy:.3f}",
        "",
        "Learned Parameters",
        str([round(float(value), 6) for value in parameters]),
        "",
        "Predictions",
    ]

    for row in rows:
        lines.append(
            f"Sample {row['sample']}: "
            f"features={row['features']} | "
            f"expected={row['expected']} | "
            f"raw_expectation={row['raw_expectation']} | "
            f"predicted={row['predicted']} | "
            f"correct={row['correct']}"
        )

    lines.extend(
        [
            "",
            "Generated Files",
            f"- {LOSS_FIGURE_PATH}",
            f"- {CIRCUIT_FIGURE_PATH}",
            "",
            "Key Takeaway",
            "Quantum Machine Learning connects classical data, quantum feature encoding,",
            "parameterized circuits, measurement, loss calculation, and classical optimization",
            "into one hybrid learning loop.",
        ]
    )

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    start = time.perf_counter()

    data, labels = create_training_data()
    trained_parameters, loss_history = train_parameters(data, labels)

    make_loss_plot(loss_history)
    make_circuit_figure(data[0], trained_parameters)
    write_report(data, labels, trained_parameters, loss_history)

    runtime = time.perf_counter() - start

    print("Day 16 Quantum Machine Learning lab complete.")
    print(f"Runtime seconds: {runtime:.4f}")
    print(f"Report written to: {REPORT_PATH}")
    print(f"Loss curve written to: {LOSS_FIGURE_PATH}")
    print(f"Circuit figure written to: {CIRCUIT_FIGURE_PATH}")


if __name__ == "__main__":
    main()