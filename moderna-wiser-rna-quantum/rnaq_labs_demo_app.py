"""Standalone RNAQ Labs 3-minute MVP demo app.

Run from project root:
    python rnaq_labs_demo_app.py
Then open:
    http://127.0.0.1:5050
"""
from __future__ import annotations

import json
from dataclasses import asdict

from flask import Flask, render_template_string, request

from src.reports.rnaq_labs_demo_packet import build_demo_packet

app = Flask(__name__)

SAMPLES = {
    "Challenge demo": {
        "sequence": "GGGAAAUCC",
        "note": "Small sequence for a fast judge/professor walkthrough.",
    },
    "Short GC-rich demo": {
        "sequence": "GGGCCCAAAUCCCGGG",
        "note": "Better for showing more candidate stems and graph conflicts.",
    },
    "Mixed synthetic demo": {
        "sequence": "AUGGCUACGGAUUCCGAU",
        "note": "Good for investor/startup storytelling because it gives a richer result.",
    },
}

AUDIENCE_GUIDE = {
    "challenge": {
        "title": "Challenge / Judge",
        "direction": "Show that the project is reproducible, benchmarked, and careful about claims.",
        "emphasize": [
            "RNA input is validated before analysis.",
            "Candidate stems become QUBO variables.",
            "Stem conflicts become graph edges.",
            "The app recommends a solver path instead of making unsupported claims.",
        ],
        "talk_track": (
            "In three minutes, I can show the full research workflow: input sequence, candidate stems, "
            "QUBO variables, graph risk, and the next validation step."
        ),
        "ask": "Ask for rubric feedback and whether the validation outputs are clear enough for final submission.",
    },
    "investor": {
        "title": "Investor / Mentor",
        "direction": "Explain the product value: turning complex scientific optimization into a clear decision report.",
        "emphasize": [
            "One input produces a structured result quickly.",
            "The system reduces confusion before deeper experiments.",
            "The output is explainable: graph risk, solver path, and safe limitations.",
            "This can become infrastructure for scientific decision workflows.",
        ],
        "talk_track": (
            "This is not just an RNA demo. It is a prototype for decision intelligence: take a complex "
            "bio-optimization problem, turn it into a QUBO, audit the graph, and recommend what to do next."
        ),
        "ask": "Ask for feedback on the first customer segment: education, research labs, biotech tooling, or AI-native discovery workflows.",
    },
    "professor": {
        "title": "Professor / Research Reviewer",
        "direction": "Show the research method, validation discipline, and limitations.",
        "emphasize": [
            "The claim is intentionally limited and auditable.",
            "Exact validation should come before larger solver claims.",
            "Graph diagnostics explain why some QUBO instances are harder.",
            "The system can connect back to the full classical benchmark pipeline.",
        ],
        "talk_track": (
            "I am using this MVP as a guided front end for the tested research pipeline. "
            "The goal is to make the assumptions, metrics, and next validation step easy to inspect."
        ),
        "ask": "Ask which validation metric or control experiment should be required before expanding the model.",
    },
    "startup": {
        "title": "YC / Startup Conversation",
        "direction": "Frame RNAQ Labs as AI-native scientific decision infrastructure.",
        "emphasize": [
            "The product is a guided discovery workflow, not just a dashboard.",
            "It converts scientific input into benchmarked optimization outputs.",
            "It keeps claims safe while still showing a path to research and commercialization.",
            "Future versions could support RNA, plant traits, protein targets, or other QUBO-ready scientific problems.",
        ],
        "talk_track": (
            "RNAQ Labs is starting as an RNA-QUBO MVP, but the bigger product direction is an AI-native "
            "scientific optimization engine that helps researchers prioritize what to test next."
        ),
        "ask": "Ask for advice on narrowing the wedge: RNA education tool, research benchmark platform, plant/agriculture optimization, or biotech decision intelligence.",
    },
    "student": {
        "title": "Student / Learner",
        "direction": "Teach the pipeline step by step.",
        "emphasize": [
            "RNA sequence input is the starting point.",
            "Base-pair candidates become possible structure pieces.",
            "QUBO variables represent choices.",
            "Graph risk explains why optimization gets difficult.",
        ],
        "talk_track": "This demo teaches how a biological sequence can become a graph and optimization problem.",
        "ask": "Ask whether the explanation is simple enough for a workshop or class demo.",
    },
}

PAGE = """
<!doctype html>
<title>RNAQ Labs 3-Minute MVP Demo</title>
<style>
  body { font-family: system-ui, Arial, sans-serif; margin: 0; background: #101418; color: #eef2f5; }
  main { max-width: 1120px; margin: 0 auto; padding: 28px; }
  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; }
  .card { border: 1px solid #2b3440; border-radius: 18px; padding: 16px; background: #161c22; margin-top: 12px; }
  label { display:block; margin: 12px 0 6px; color: #b9c3cf; }
  input, select { width: 100%; box-sizing: border-box; border-radius: 12px; border: 1px solid #394452; padding: 10px; background:#0e1318; color:#fff; }
  button { border: 0; border-radius: 12px; padding: 11px 14px; margin-top: 14px; background: #70a5ff; color: #08111f; font-weight: 700; cursor:pointer; }
  .muted { color: #a6b0bc; }
  .value { font-size: 1.55rem; font-weight: 800; }
  .safe { border-left: 4px solid #70a5ff; padding-left: 12px; }
  .pill { display: inline-block; border: 1px solid #3a4655; border-radius: 999px; padding: 6px 10px; margin: 4px 4px 4px 0; color: #dce7f5; background:#0e1318; }
  .step { border-left: 3px solid #70a5ff; padding-left: 12px; margin: 10px 0; }
  pre { white-space: pre-wrap; overflow-wrap: anywhere; background:#0e1318; border-radius:14px; padding: 14px; }
</style>
<main>
  <h1>RNAQ Labs: 3-Minute MVP Demo</h1>
  <p class="muted">Paste one RNA sequence, pick the audience, and generate a clear challenge/investor/professor/startup explanation.</p>

  <section class="card safe">
    <h2>Start here</h2>
    <div class="grid">
      <div class="step"><strong>1. Choose input</strong><br><span class="muted">Use a sample sequence for a clean demo, or paste your own RNA sequence.</span></div>
      <div class="step"><strong>2. Pick audience</strong><br><span class="muted">The app changes the talk track depending on who you are presenting to.</span></div>
      <div class="step"><strong>3. Generate result</strong><br><span class="muted">Show sequence length, candidate stems, QUBO variables, graph risk, and recommended solver path.</span></div>
    </div>
  </section>

  <section class="card">
    <h2>3-minute demo timer</h2>
    <div class="grid">
      <div class="step"><strong>0:00-0:30</strong><br><span class="muted">Problem: RNA/scientific optimization is complex and hard to explain.</span></div>
      <div class="step"><strong>0:30-1:20</strong><br><span class="muted">Input: choose a sequence and audience, then generate the result.</span></div>
      <div class="step"><strong>1:20-2:20</strong><br><span class="muted">Pipeline: stems to QUBO variables to graph conflicts to solver path.</span></div>
      <div class="step"><strong>2:20-3:00</strong><br><span class="muted">Close: safe claim, next milestone, and what feedback you want.</span></div>
    </div>
  </section>

  <form method="post" class="card">
    <label for="sample">Sample input</label>
    <select id="sample" name="sample">
      <option value="">Choose a sample or paste your own</option>
      {% for name, item in samples.items() %}
      <option value="{{ item.sequence }}" {% if item.sequence == sequence %}selected{% endif %}>{{ name }} - {{ item.sequence }}</option>
      {% endfor %}
    </select>
    <p class="muted" id="sample-note">Tip: choose a sample for a clean demo, or paste your own sequence below.</p>

    <label for="sequence">RNA sequence</label>
    <input id="sequence" name="sequence" value="{{ sequence }}" placeholder="Example: GGGAAAUCC" />

    <label for="audience">Audience</label>
    <select id="audience" name="audience">
      {% for key, guide in audience_guide.items() %}
      <option value="{{ key }}" {% if key == audience %}selected{% endif %}>{{ guide.title }}</option>
      {% endfor %}
    </select>

    <button type="submit">Generate demo result</button>
  </form>

  <section class="card">
    <h2>Audience playbook: {{ guide.title }}</h2>
    <p><strong>Direction:</strong> {{ guide.direction }}</p>
    <p><strong>Talk track:</strong> {{ guide.talk_track }}</p>
    <p><strong>What to ask for next:</strong> {{ guide.ask }}</p>
    <div>
      {% for item in guide.emphasize %}
      <span class="pill">{{ item }}</span>
      {% endfor %}
    </div>
  </section>

  {% if error %}
  <div class="card"><strong>Error:</strong> {{ error }}</div>
  {% endif %}

  {% if result %}
  <section class="grid" aria-label="MVP metrics">
    <div class="card"><div class="muted">Sequence length</div><div class="value">{{ result.sequence_length }}</div></div>
    <div class="card"><div class="muted">Candidate stems</div><div class="value">{{ result.candidate_stem_count }}</div></div>
    <div class="card"><div class="muted">QUBO variables</div><div class="value">{{ result.qubo_variable_count }}</div></div>
    <div class="card"><div class="muted">Graph risk</div><div class="value">{{ result.graph_risk_label }}</div></div>
  </section>

  <section class="card">
    <h2>What happened</h2>
    <p>The sequence was validated, candidate base pairs and stems were generated, stems were treated as QUBO variables, and stem conflicts were treated as graph edges.</p>
    <p><strong>Recommended path:</strong> {{ result.suggested_solver_path }}</p>
  </section>

  <section class="card">
    <h2>3-minute story</h2>
    <ol>{% for item in result.three_minute_story %}<li>{{ item }}</li>{% endfor %}</ol>
  </section>

  <section class="card safe">
    <h2>Safe claim</h2>
    <p>{{ result.safe_claim }}</p>
  </section>

  <section class="card">
    <h2>Next milestone</h2>
    <p>{{ result.next_milestone }}</p>
  </section>

  <section class="card">
    <h2>Result JSON</h2>
    <pre>{{ result_json }}</pre>
  </section>
  {% endif %}

  <section class="card">
    <h2>Best demo close</h2>
    <p>
      RNAQ Labs is a guided decision-intelligence layer for scientific optimization.
      The MVP shows how one sequence becomes candidate structures, QUBO variables,
      graph risk, and a solver recommendation. The safe goal is not to claim quantum
      advantage; the goal is to make the optimization workflow auditable and easy to review.
    </p>
  </section>
</main>
<script>
  const samples = {{ sample_json|safe }};
  const sampleSelect = document.getElementById("sample");
  const sequenceInput = document.getElementById("sequence");
  const sampleNote = document.getElementById("sample-note");

  sampleSelect.addEventListener("change", function () {
    const selected = sampleSelect.value;
    if (!selected) {
      sampleNote.textContent = "Tip: choose a sample for a clean demo, or paste your own sequence below.";
      return;
    }
    sequenceInput.value = selected;
    const found = Object.values(samples).find(item => item.sequence === selected);
    sampleNote.textContent = found ? found.note : "Sample selected.";
  });
</script>
"""


@app.route("/", methods=["GET", "POST"])
def home():
    sequence = request.form.get("sequence", "GGGAAAUCC")
    audience = request.form.get("audience", "challenge")
    if audience not in AUDIENCE_GUIDE:
        audience = "challenge"

    error = None
    result = None
    result_json = ""

    if request.method == "POST":
        try:
            packet_audience = audience if audience in {"challenge", "investor", "professor"} else "investor"
            result = build_demo_packet(sequence, audience=packet_audience, label="web_demo")
            result_json = json.dumps(asdict(result), indent=2)
        except Exception as exc:  # noqa: BLE001 - show useful demo error in UI
            error = str(exc)

    return render_template_string(
        PAGE,
        samples=SAMPLES,
        sample_json=json.dumps(SAMPLES),
        sequence=sequence,
        audience=audience,
        audience_guide=AUDIENCE_GUIDE,
        guide=AUDIENCE_GUIDE[audience],
        error=error,
        result=result,
        result_json=result_json,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=True)
