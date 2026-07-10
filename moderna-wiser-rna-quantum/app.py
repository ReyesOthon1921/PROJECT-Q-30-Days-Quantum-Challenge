from flask import Flask, render_template, request, jsonify

from src.classical.dotbracket import (
    validate_dotbracket,
    dotbracket_to_pairs,
    summarize_structure,
)
from src.evaluation.solver_comparison import compare_solvers
from src.classical.sequence_tools import summarize_sequence
from src.classical.vienna_benchmark import run_vienna_benchmark

from src.qubo.candidate_pairs import summarize_candidate_pairs
from src.qubo.candidate_stems import summarize_candidate_stems
from src.qubo.build_qubo import build_stem_qubo

from src.solvers.greedy_solver import solve_stem_qubo_greedy
from src.solvers.simulated_annealing import solve_stem_qubo_simulated_annealing

from src.evaluation.metrics import evaluate_greedy_against_vienna
from src.evaluation.scaling import run_and_save_scaling_experiment


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/validate-sequence", methods=["POST"])
def validate_sequence():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        summary = summarize_sequence(sequence)
        return jsonify({"success": True, "summary": summary})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/run-vienna", methods=["POST"])
def run_vienna():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_vienna_benchmark(sequence)
        return jsonify(result)

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/candidate-pairs", methods=["POST"])
def candidate_pairs():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        summary = summarize_candidate_pairs(sequence)
        return jsonify({"success": True, "summary": summary})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/candidate-stems", methods=["POST"])
def candidate_stems():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        summary = summarize_candidate_stems(sequence)
        return jsonify({"success": True, "summary": summary})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/build-qubo", methods=["POST"])
def build_qubo():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        qubo = build_stem_qubo(sequence)
        return jsonify({"success": True, "qubo": qubo})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/solve-greedy", methods=["POST"])
def solve_greedy():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = solve_stem_qubo_greedy(sequence)
        return jsonify({"success": True, "result": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/solve-annealing", methods=["POST"])
def solve_annealing():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = solve_stem_qubo_simulated_annealing(sequence)
        return jsonify({"success": True, "result": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/evaluate-greedy", methods=["POST"])
def evaluate_greedy():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = evaluate_greedy_against_vienna(sequence)
        return jsonify({"success": True, "evaluation": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/run-scaling", methods=["POST"])
def run_scaling():
    try:
        result = run_and_save_scaling_experiment()
        return jsonify(result)

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/validate-structure", methods=["POST"])
def validate_structure():
    data = request.get_json() or {}

    sequence = data.get("sequence", "").strip().upper()
    structure = data.get("structure", "").strip()

    if not sequence or not structure:
        return jsonify(
            {
                "success": False,
                "error": "Please enter both an RNA sequence and a dot-bracket structure.",
            }
        ), 400

    if len(sequence) != len(structure):
        return jsonify(
            {
                "success": False,
                "error": "Sequence and structure must have the same length.",
                "sequence_length": len(sequence),
                "structure_length": len(structure),
            }
        ), 400

    try:
        if not validate_dotbracket(structure):
            return jsonify(
                {
                    "success": False,
                    "error": "Invalid dot-bracket structure. Use only dots and balanced parentheses.",
                }
            ), 400

        summary = summarize_structure(sequence, structure)
        return jsonify({"success": True, "summary": summary})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/pairs", methods=["POST"])
def get_pairs():
    data = request.get_json() or {}
    structure = data.get("structure", "").strip()

    try:
        pairs = dotbracket_to_pairs(structure)
        return jsonify(
            {
                "success": True,
                "pairs": pairs,
                "num_pairs": len(pairs),
            }
        )

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 400

@app.route("/api/compare-solvers", methods=["POST"])
def compare_solver_results():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = compare_solvers(sequence)
        return jsonify({"success": True, "comparison": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


if __name__ == "__main__":
    app.run(debug=True)