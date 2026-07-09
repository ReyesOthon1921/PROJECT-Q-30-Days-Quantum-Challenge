from flask import Flask, render_template, request, jsonify

from src.classical.dotbracket import (
    validate_dotbracket,
    dotbracket_to_pairs,
    summarize_structure,
)

from src.classical.sequence_tools import summarize_sequence
from src.classical.vienna_benchmark import run_vienna_benchmark


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

        return jsonify(
            {
                "success": True,
                "summary": summary,
            }
        )

    except Exception as error:
        return jsonify(
            {
                "success": False,
                "error": str(error),
            }
        ), 500


@app.route("/api/run-vienna", methods=["POST"])
def run_vienna():
    data = request.get_json() or {}
    sequence = data.get("sequence", "")

    try:
        result = run_vienna_benchmark(sequence)
        return jsonify(result)

    except Exception as error:
        return jsonify(
            {
                "success": False,
                "error": str(error),
            }
        ), 500


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

        return jsonify(
            {
                "success": True,
                "summary": summary,
            }
        )

    except Exception as error:
        return jsonify(
            {
                "success": False,
                "error": str(error),
            }
        ), 500


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
        return jsonify(
            {
                "success": False,
                "error": str(error),
            }
        ), 400


if __name__ == "__main__":
    app.run(debug=True)