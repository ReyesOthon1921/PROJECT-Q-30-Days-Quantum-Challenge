function scrollToSection(id) {
    document.getElementById(id).scrollIntoView({ behavior: "smooth" });
}

function getSequence() {
    return document.getElementById("sequence").value.trim();
}

function getStructure() {
    return document.getElementById("structure").value.trim();
}

function setMetric(id, value) {
    const element = document.getElementById(id);

    if (!element) {
        return;
    }

    if (value === undefined || value === null || value === "") {
        element.textContent = "—";
    } else {
        element.textContent = value;
    }
}

function findSolverRow(comparisonRows, keyword) {
    if (!comparisonRows) {
        return null;
    }

    return comparisonRows.find((row) =>
        row.solver && row.solver.toLowerCase().includes(keyword)
    );
}

function updateSummaryCards(data) {
    const mfe =
        data?.mfe_energy ??
        data?.comparison?.vienna_mfe_energy ??
        data?.evaluation?.vienna_mfe_energy ??
        null;

    const quboVariables =
        data?.qubo?.num_variables ??
        data?.qubo?.estimated_qubits ??
        data?.result?.total_qubo_variables ??
        data?.summary?.estimated_binary_variables ??
        data?.summary?.candidate_stem_count ??
        null;

    const estimatedQubits =
        data?.qubo?.estimated_qubits ??
        data?.result?.total_qubo_variables ??
        data?.summary?.estimated_qubits ??
        null;

    const greedyF1 =
        data?.evaluation?.metrics?.f1_score ??
        data?.comparison?.greedy_evaluation?.metrics?.f1_score ??
        findSolverRow(data?.comparison?.comparison_rows, "greedy")?.f1_score ??
        null;

    const annealingF1 =
        data?.comparison?.annealing_evaluation?.metrics?.f1_score ??
        findSolverRow(data?.comparison?.comparison_rows, "annealing")?.f1_score ??
        null;

    const bestSolver =
        data?.comparison?.best_solver_by_f1?.solver ??
        null;

    if (mfe !== null) {
        setMetric("metric-mfe", Number(mfe).toFixed(3));
    }

    if (quboVariables !== null) {
        setMetric("metric-variables", quboVariables);
    }

    if (estimatedQubits !== null) {
        setMetric("metric-qubits", estimatedQubits);
    }

    if (greedyF1 !== null) {
        setMetric("metric-greedy-f1", greedyF1);
    }

    if (annealingF1 !== null) {
        setMetric("metric-annealing-f1", annealingF1);
    }

    if (bestSolver !== null) {
        setMetric("metric-best-solver", bestSolver.replace(" stem-QUBO baseline", ""));
    }
}

function showResults(data) {
    const resultsBox = document.getElementById("results");
    resultsBox.textContent = JSON.stringify(data, null, 2);

    updateSummaryCards(data);
    renderFromResponse(data);
}

async function postJson(url, payload, loadingMessage) {
    const resultsBox = document.getElementById("results");
    resultsBox.textContent = loadingMessage;

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        showResults(data);
    } catch (error) {
        resultsBox.textContent = "Frontend error: " + error;
    }
}

async function analyzeSequence() {
    await postJson(
        "/api/validate-sequence",
        { sequence: getSequence() },
        "Analyzing RNA sequence..."
    );
}

async function runViennaBenchmark() {
    await postJson(
        "/api/run-vienna",
        { sequence: getSequence() },
        "Running ViennaRNA benchmark..."
    );
}

async function generateCandidatePairs() {
    await postJson(
        "/api/candidate-pairs",
        { sequence: getSequence() },
        "Generating candidate base-pair variables..."
    );
}

async function generateCandidateStems() {
    await postJson(
        "/api/candidate-stems",
        { sequence: getSequence() },
        "Generating candidate stem variables..."
    );
}

async function buildQubo() {
    await postJson(
        "/api/build-qubo",
        { sequence: getSequence() },
        "Building stem-based QUBO..."
    );
}

async function runGreedySolver() {
    await postJson(
        "/api/solve-greedy",
        { sequence: getSequence() },
        "Running greedy stem-QUBO solver..."
    );
}

async function runAnnealingSolver() {
    await postJson(
        "/api/solve-annealing",
        { sequence: getSequence() },
        "Running simulated annealing stem-QUBO solver..."
    );
}

async function evaluateGreedy() {
    await postJson(
        "/api/evaluate-greedy",
        { sequence: getSequence() },
        "Evaluating greedy solver against ViennaRNA..."
    );
}

async function compareSolvers() {
    await postJson(
        "/api/compare-solvers",
        { sequence: getSequence() },
        "Comparing solvers against ViennaRNA..."
    );
}

async function runScalingAnalysis() {
    await postJson(
        "/api/run-scaling",
        {},
        "Running scaling analysis..."
    );
}

async function validateStructure() {
    await postJson(
        "/api/validate-structure",
        {
            sequence: getSequence(),
            structure: getStructure()
        },
        "Validating dot-bracket RNA structure..."
    );
}

function dotBracketToPairs(structure) {
    const stack = [];
    const pairs = [];

    for (let index = 0; index < structure.length; index++) {
        const char = structure[index];

        if (char === "(") {
            stack.push(index);
        }

        if (char === ")") {
            const left = stack.pop();

            if (left !== undefined) {
                pairs.push([left, index]);
            }
        }
    }

    return pairs;
}

function findStructureInResponse(data) {
    return (
        data?.summary?.structure ||
        data?.structure ||
        data?.result?.predicted_structure ||
        data?.evaluation?.greedy_structure ||
        data?.comparison?.annealing_evaluation?.predicted_structure ||
        data?.comparison?.greedy_evaluation?.predicted_structure ||
        data?.comparison?.vienna_structure ||
        getStructure()
    );
}

function renderFromResponse(data) {
    const sequence = getSequence();
    const structure = findStructureInResponse(data);

    drawRnaSimulation(sequence, structure);
}

function drawCurrentInput() {
    drawRnaSimulation(getSequence(), getStructure());
}

function drawRnaSimulation(sequence, structure) {
    const canvas = document.getElementById("rnaCanvas");

    if (!canvas) {
        return;
    }

    const ctx = canvas.getContext("2d");

    const width = canvas.width;
    const height = canvas.height;

    ctx.clearRect(0, 0, width, height);

    const gradient = ctx.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, "#000000");
    gradient.addColorStop(0.35, "#2A0048");
    gradient.addColorStop(0.7, "#800080");
    gradient.addColorStop(1, "#D50048");

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    if (!sequence) {
        ctx.fillStyle = "#ffffff";
        ctx.font = "28px Arial";
        ctx.fillText("Enter an RNA sequence to visualize.", 40, 80);
        return;
    }

    const cleanSequence = sequence.replace(/\s/g, "").toUpperCase();
    const cleanStructure = structure || ".".repeat(cleanSequence.length);
    const pairs = dotBracketToPairs(cleanStructure);

    const margin = 70;
    const usableWidth = width - margin * 2;
    const centerY = height * 0.58;
    const spacing = usableWidth / Math.max(cleanSequence.length - 1, 1);

    const positions = [];

    for (let i = 0; i < cleanSequence.length; i++) {
        const x = margin + i * spacing;
        const wave = Math.sin(i * 0.65) * 38;
        const y = centerY + wave;
        positions.push({ x, y });
    }

    for (const [i, j] of pairs) {
        if (!positions[i] || !positions[j]) {
            continue;
        }

        const start = positions[i];
        const end = positions[j];
        const midX = (start.x + end.x) / 2;
        const arcHeight = Math.min(150, 30 + Math.abs(end.x - start.x) * 0.22);

        ctx.beginPath();
        ctx.moveTo(start.x, start.y);
        ctx.quadraticCurveTo(midX, centerY - arcHeight, end.x, end.y);
        ctx.strokeStyle = "rgba(255, 120, 180, 0.75)";
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    ctx.beginPath();

    for (let i = 0; i < positions.length; i++) {
        const point = positions[i];

        if (i === 0) {
            ctx.moveTo(point.x, point.y);
        } else {
            ctx.lineTo(point.x, point.y);
        }
    }

    ctx.strokeStyle = "rgba(255, 255, 255, 0.55)";
    ctx.lineWidth = 3;
    ctx.stroke();

    for (let i = 0; i < positions.length; i++) {
        const point = positions[i];
        const base = cleanSequence[i];

        const nodeGradient = ctx.createRadialGradient(
            point.x - 4,
            point.y - 5,
            2,
            point.x,
            point.y,
            14
        );

        nodeGradient.addColorStop(0, "#ffffff");
        nodeGradient.addColorStop(0.45, "#D50048");
        nodeGradient.addColorStop(1, "#560072");

        ctx.beginPath();
        ctx.arc(point.x, point.y, 13, 0, Math.PI * 2);
        ctx.fillStyle = nodeGradient;
        ctx.fill();

        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 11px Arial";
        ctx.textAlign = "center";
        ctx.fillText(base, point.x, point.y + 4);
    }

    ctx.textAlign = "left";
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 24px Arial";
    ctx.fillText("RNA Secondary Structure Simulation", 34, 44);

    ctx.font = "15px Arial";
    ctx.fillStyle = "rgba(255,255,255,0.8)";
    ctx.fillText(`Length: ${cleanSequence.length} bases`, 34, 72);
    ctx.fillText(`Base pairs shown: ${pairs.length}`, 34, 94);
}

window.addEventListener("load", () => {
    drawCurrentInput();
});