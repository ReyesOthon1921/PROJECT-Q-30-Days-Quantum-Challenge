async function analyzeSequence() {
    const sequence = document.getElementById("sequence").value;
    const resultsBox = document.getElementById("results");

    resultsBox.textContent = "Analyzing RNA sequence...";

    try {
        const response = await fetch("/api/validate-sequence", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ sequence: sequence })
        });

        const data = await response.json();
        resultsBox.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        resultsBox.textContent = "Frontend error: " + error;
    }
}


async function runViennaBenchmark() {
    const sequence = document.getElementById("sequence").value;
    const resultsBox = document.getElementById("results");

    resultsBox.textContent = "Running classical benchmark...";

    try {
        const response = await fetch("/api/run-vienna", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ sequence: sequence })
        });

        const data = await response.json();
        resultsBox.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        resultsBox.textContent = "Frontend error: " + error;
    }
}


async function generateCandidatePairs() {
    const sequence = document.getElementById("sequence").value;
    const resultsBox = document.getElementById("results");

    resultsBox.textContent = "Generating candidate base-pair variables...";

    try {
        const response = await fetch("/api/candidate-pairs", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ sequence: sequence })
        });

        const data = await response.json();
        resultsBox.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        resultsBox.textContent = "Frontend error: " + error;
    }
}


async function generateCandidateStems() {
    const sequence = document.getElementById("sequence").value;
    const resultsBox = document.getElementById("results");

    resultsBox.textContent = "Generating candidate stem variables...";

    try {
        const response = await fetch("/api/candidate-stems", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ sequence: sequence })
        });

        const data = await response.json();
        resultsBox.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        resultsBox.textContent = "Frontend error: " + error;
    }
}

async function buildQubo() {
    const sequence = document.getElementById("sequence").value;
    const resultsBox = document.getElementById("results");

    resultsBox.textContent = "Building stem-based QUBO...";

    try {
        const response = await fetch("/api/build-qubo", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ sequence: sequence })
        });

        const data = await response.json();
        resultsBox.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        resultsBox.textContent = "Frontend error: " + error;
    }
}


async function runGreedySolver() {
    const sequence = document.getElementById("sequence").value;
    const resultsBox = document.getElementById("results");

    resultsBox.textContent = "Running greedy stem-QUBO solver...";

    try {
        const response = await fetch("/api/solve-greedy", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ sequence: sequence })
        });

        const data = await response.json();
        resultsBox.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        resultsBox.textContent = "Frontend error: " + error;
    }
}

async function evaluateGreedy() {
    const sequence = document.getElementById("sequence").value;
    const resultsBox = document.getElementById("results");

    resultsBox.textContent = "Evaluating greedy solver against ViennaRNA...";

    try {
        const response = await fetch("/api/evaluate-greedy", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ sequence: sequence })
        });

        const data = await response.json();
        resultsBox.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        resultsBox.textContent = "Frontend error: " + error;
    }
}

async function validateStructure() {
    const sequence = document.getElementById("sequence").value;
    const structure = document.getElementById("structure").value;
    const resultsBox = document.getElementById("results");

    resultsBox.textContent = "Running structure validation...";

    try {
        const response = await fetch("/api/validate-structure", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                sequence: sequence,
                structure: structure
            })
        });

        const data = await response.json();
        resultsBox.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        resultsBox.textContent = "Frontend error: " + error;
    }
}