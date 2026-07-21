from flask import Flask, jsonify, render_template, request

from src.classical.dotbracket import (
    summarize_structure,
    validate_dotbracket,
)

from src.evaluation.qubit_compression_estimator import run_qubit_compression_estimator
from src.evaluation.qrao_subset_mapping import run_qrao_subset_mapping
from src.evaluation.vqe_parameter_sweep import run_vqe_parameter_sweep
from src.evaluation.measured_bitstring_energy import run_measured_bitstring_energy
from src.evaluation.hardware_readiness import run_hardware_readiness_check
from src.evaluation.qaoa_parameter_sweep import run_qaoa_parameter_sweep
from src.evaluation.circuit_comparison import run_circuit_comparison
from src.quantum.vqe_circuit import run_vqe_circuit_simulation
from src.quantum.qaoa_circuit import run_qaoa_circuit_simulation
from src.evaluation.quantum_benchmark import run_quantum_benchmark
from src.evaluation.bioinformatics_metrics import run_bioinformatics_metrics
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

@app.route("/api/bioinformatics-metrics", methods=["POST"])
def bioinformatics_metrics():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_bioinformatics_metrics(sequence)
        return jsonify({"success": True, "bioinformatics_metrics": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500

@app.route("/api/quantum-benchmark", methods=["POST"])
def quantum_benchmark():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_quantum_benchmark(sequence)
        return jsonify({"success": True, "quantum_benchmark": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500

@app.route("/api/qaoa-circuit", methods=["POST"])
def qaoa_circuit():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_qaoa_circuit_simulation(sequence)
        return jsonify({"success": True, "qaoa_circuit": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/vqe-circuit", methods=["POST"])
def vqe_circuit():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_vqe_circuit_simulation(sequence)
        return jsonify({"success": True, "vqe_circuit": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500

@app.route("/api/circuit-comparison", methods=["POST"])
def circuit_comparison():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_circuit_comparison(sequence)
        return jsonify({"success": True, "circuit_comparison": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500

@app.route("/api/qaoa-parameter-sweep", methods=["POST"])
def qaoa_parameter_sweep():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_qaoa_parameter_sweep(sequence)
        return jsonify({"success": True, "qaoa_parameter_sweep": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500

@app.route("/api/vqe-parameter-sweep", methods=["POST"])
def vqe_parameter_sweep():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_vqe_parameter_sweep(sequence)
        return jsonify({"success": True, "vqe_parameter_sweep": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/measured-bitstring-energy", methods=["POST"])
def measured_bitstring_energy():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_measured_bitstring_energy(sequence)
        return jsonify({"success": True, "measured_bitstring_energy": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/hardware-readiness", methods=["POST"])
def hardware_readiness():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_hardware_readiness_check(sequence)
        return jsonify({"success": True, "hardware_readiness": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500

@app.route("/api/qubit-compression-estimator", methods=["POST"])
def qubit_compression_estimator():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_qubit_compression_estimator(sequence)
        return jsonify({"success": True, "qubit_compression_estimator": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500


@app.route("/api/qrao-subset-mapping", methods=["POST"])
def qrao_subset_mapping():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_qrao_subset_mapping(sequence)
        return jsonify({"success": True, "qrao_subset_mapping": result})

    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500





# PHASE42_EXACT_VALIDATION_DASHBOARD_ROUTE
@app.route("/api/exact-validation-dashboard", methods=["GET"])
def exact_validation_dashboard_api():
    from flask import jsonify
    from src.evaluation.exact_validation_dashboard import run_exact_validation_dashboard

    try:
        result = run_exact_validation_dashboard()
        return jsonify(result)
    except Exception as error:
        return jsonify({"success": False, "error": str(error)}), 500

# === RNAQ Labs guided demo route BEGIN ===
# Live route for the 3-minute guided MVP demo.
# This keeps the main Flask dashboard deployed through wsgi:app,
# while exposing the demo at /mvp-demo and /rnaq-demo.
import json as _rnaq_json
from dataclasses import asdict as _rnaq_asdict
from flask import render_template_string as _rnaq_render_template_string, request as _rnaq_request

from rnaq_labs_demo_app import (
    PAGE as _RNAQ_DEMO_PAGE,
    SAMPLES as _RNAQ_DEMO_SAMPLES,
    AUDIENCE_GUIDE as _RNAQ_DEMO_AUDIENCE_GUIDE,
)
from src.reports.rnaq_labs_demo_packet import build_demo_packet as _rnaq_build_demo_packet


@app.route('/mvp-demo', methods=['GET', 'POST'])
@app.route('/rnaq-demo', methods=['GET', 'POST'])
def rnaq_labs_guided_demo():
    sequence = _rnaq_request.form.get('sequence', 'GGGAAAUCC')
    audience = _rnaq_request.form.get('audience', 'challenge')

    if audience not in _RNAQ_DEMO_AUDIENCE_GUIDE:
        audience = 'challenge'

    error = None
    result = None
    result_json = ''

    if _rnaq_request.method == 'POST':
        try:
            packet_audience = audience if audience in {'challenge', 'investor', 'professor'} else 'investor'
            result = _rnaq_build_demo_packet(sequence, audience=packet_audience, label='web_demo')
            result_json = _rnaq_json.dumps(_rnaq_asdict(result), indent=2)
        except Exception as exc:  # Keep the demo UI safe during live walkthroughs.
            error = str(exc)

    return _rnaq_render_template_string(
        _RNAQ_DEMO_PAGE,
        samples=_RNAQ_DEMO_SAMPLES,
        sample_json=_rnaq_json.dumps(_RNAQ_DEMO_SAMPLES),
        sequence=sequence,
        audience=audience,
        audience_guide=_RNAQ_DEMO_AUDIENCE_GUIDE,
        guide=_RNAQ_DEMO_AUDIENCE_GUIDE[audience],
        error=error,
        result=result,
        result_json=result_json,
    )
# === RNAQ Labs guided demo route END ===

if __name__ == "__main__":
    app.run(debug=True)