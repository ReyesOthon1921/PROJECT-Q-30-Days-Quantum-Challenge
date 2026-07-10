from flask import Flask, jsonify, render_template, request

from src.classical.dotbracket import (
    summarize_structure,
    validate_dotbracket,
)
from src.classical.sequence_tools import summarize_sequence
from src.classical.vienna_benchmark import run_vienna_benchmark
from src.qubo.candidate_pairs import summarize_candidate_pairs
from src.qubo.candidate_stems import summarize_candidate_stems
from src.qubo.build_qubo import build_stem_qubo
from src.solvers.greedy_solver import solve_stem_qubo_greedy
from src.solvers.simulated_annealing import solve_stem_qubo_simulated_annealing
from src.solvers.qaoa_prototype import run_qaoa_readiness_demo
from src.solvers.vqe_prototype import run_vqe_readiness_demo
from src.evaluation.metrics import evaluate_greedy_against_vienna
from src.evaluation.scaling import run_and_save_scaling_experiment
from src.evaluation.solver_comparison import compare_solvers
from src.evaluation.plot_graphs import run_plot_generation
from src.evaluation.algorithm_comparison_graphs import run_algorithm_comparison_graphs


app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return "", 204


@app.route("/api/validate-sequence", methods=["POST"])
def validate_sequence():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        summary = summarize_sequence(sequence)
        return jsonify({"success": True, "summary": summary})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/validate-structure", methods=["POST"])
def validate_structure():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")
    structure = data.get("structure", "")

    try:
        is_valid = validate_dotbracket(structure)
        summary = summarize_structure(sequence, structure)

        return jsonify({
            "success": True,
            "is_valid_dotbracket": is_valid,
            "summary": summary,
        })

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/run-vienna", methods=["POST"])
def run_vienna():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_vienna_benchmark(sequence)
        return jsonify({"success": True, **result})

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
        evaluation = evaluate_greedy_against_vienna(sequence)
        return jsonify({"success": True, "evaluation": evaluation})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/compare-solvers", methods=["POST"])
def compare_solver_results():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = compare_solvers(sequence)
        return jsonify({"success": True, "comparison": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/run-scaling", methods=["POST"])
def run_scaling():
    try:
        result = run_and_save_scaling_experiment()
        return jsonify({"success": True, "scaling": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/qaoa-readiness", methods=["POST"])
def qaoa_readiness():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_qaoa_readiness_demo(sequence)
        return jsonify({"success": True, "qaoa_readiness": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/vqe-readiness", methods=["POST"])
def vqe_readiness():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_vqe_readiness_demo(sequence)
        return jsonify({"success": True, "vqe_readiness": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/generate-graphs", methods=["POST"])
def generate_graphs():
    try:
        result = run_plot_generation()
        return jsonify({"success": True, "graphs": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/algorithm-comparison-graphs", methods=["POST"])
def algorithm_comparison_graphs():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_algorithm_comparison_graphs(sequence)
        return jsonify({"success": True, "algorithm_graphs": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


if __name__ == "__main__":
    app.run(debug=True)