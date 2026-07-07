"""
Mini Project 2 — Quantum Communication Dashboard

Flask web application that runs Qiskit simulations for:

1. Bell States
2. Quantum Entanglement
3. Quantum Teleportation
"""

from flask import Flask, render_template

from quantum.circuits import (
    run_bell_state,
    run_entanglement,
    run_teleportation,
)


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/bell")
def bell():
    result = run_bell_state()
    return render_template("result.html", result=result)


@app.route("/entanglement")
def entanglement():
    result = run_entanglement()
    return render_template("result.html", result=result)


@app.route("/teleportation")
def teleportation():
    result = run_teleportation()
    return render_template("result.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)