import {
  Activity,
  Beaker,
  BookOpen,
  Bug,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Download,
  Leaf,
  Microscope,
  Plus,
  Search,
  ShieldCheck,
  Sprout,
  TestTube2,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";
import Sparkline from "./Sparkline";
import SoilResearchExtensions from "./SoilResearchExtensions";

const tabs = [
  "Soil Food Web Overview",
  "Microbial Biomass",
  "Soil Fauna",
  "Mycorrhizae",
  "Nutrient Cycling",
  "Compost Biology",
  "Soil Structure & Water",
  "Soil Chemistry",
  "Research Source Registry",
  "Sample Provenance",
  "Sensor Fusion",
  "Sample Graph",
  "Sampling Optimizer",
  "Future Research",
  "Methods & References",
];

const extendedTabs = new Set([
  "Soil Structure & Water",
  "Soil Chemistry",
  "Research Source Registry",
  "Sample Provenance",
  "Sensor Fusion",
  "Sample Graph",
  "Sampling Optimizer",
  "Future Research",
]);

const initialObservations = [
  {
    id: "SFW-001",
    date: "2026-07-24",
    zone: "North Control",
    method: "Direct microscopy",
    fungi: 812,
    bacteria: 512,
    protozoa: 320,
    nematodes: 42,
    mycorrhizae: 68,
    ratio: 1.6,
    bhi: 78,
    notes: "Compost extract treatment under review.",
  },
  {
    id: "SFW-002",
    date: "2026-07-22",
    zone: "Beneficial Zone",
    method: "Direct microscopy",
    fungi: 745,
    bacteria: 485,
    protozoa: 298,
    nematodes: 38,
    mycorrhizae: 64,
    ratio: 1.5,
    bhi: 72,
    notes: "Mulch and beneficial inoculant comparison.",
  },
  {
    id: "SFW-003",
    date: "2026-07-20",
    zone: "Untreated Control",
    method: "Direct microscopy",
    fungi: 312,
    bacteria: 598,
    protozoa: 112,
    nematodes: 24,
    mycorrhizae: 32,
    ratio: 0.5,
    bhi: 54,
    notes: "No amendment; baseline reference.",
  },
  {
    id: "SFW-004",
    date: "2026-07-18",
    zone: "Compost Trial",
    method: "Compost microscopy",
    fungi: 922,
    bacteria: 498,
    protozoa: 351,
    nematodes: 47,
    mycorrhizae: 71,
    ratio: 1.9,
    bhi: 81,
    notes: "Compost maturity trial.",
  },
  {
    id: "SFW-005",
    date: "2026-07-16",
    zone: "Cover Crop Zone",
    method: "Root staining",
    fungi: 689,
    bacteria: 476,
    protozoa: 276,
    nematodes: 36,
    mycorrhizae: 59,
    ratio: 1.4,
    bhi: 69,
    notes: "Cover-crop root colonization check.",
  },
];

const soilTasks = [
  ["Collect soil sample — North Control", "Jul 27", "Sampling"],
  ["Microscope analysis — Batch 12", "Jul 28", "Lab"],
  ["Compost maturity check", "Jul 29", "Quality"],
  ["Root colonization scoring", "Jul 30", "Mycorrhizae"],
];

const focusPanels = {
  "Microbial Biomass": {
    icon: Microscope,
    title: "Microbial biomass workspace",
    description:
      "Track fungal and bacterial biomass, document the microscopy method, and compare treatment plots against untreated controls.",
    measurements: [
      "Fungal biomass",
      "Bacterial biomass",
      "Fungal-to-bacterial ratio",
      "Analyst confidence",
      "Sample dilution and field metadata",
    ],
    method:
      "Use one frozen sampling and counting protocol per experiment. Record analyst, magnification, dilution, field moisture, and image evidence.",
    caution:
      "The dashboard score is a prototype research index. It is not a laboratory diagnosis or a substitute for validated agronomic testing.",
  },
  "Soil Fauna": {
    icon: Bug,
    title: "Soil fauna workspace",
    description:
      "Monitor protozoa and nematode activity as part of the living soil network and nutrient-cycling evidence chain.",
    measurements: [
      "Amoebae and flagellate counts",
      "Ciliate observations",
      "Bacterial-feeding nematodes",
      "Fungal-feeding nematodes",
      "Predator and pest flags",
    ],
    method:
      "Record organisms by functional group, preserve images, and compare counts using the same extraction and observation procedure.",
    caution:
      "Species-level conclusions require qualified identification. AgroQ stores functional-group observations and confidence levels.",
  },
  Mycorrhizae: {
    icon: Sprout,
    title: "Mycorrhizal colonization workspace",
    description:
      "Connect root-colonization observations with plant vigor, treatment history, soil moisture, and experimental outcomes.",
    measurements: [
      "Percent root colonization",
      "Root sample location",
      "Staining protocol",
      "Crop and growth stage",
      "Linked treatment and control",
    ],
    method:
      "Use repeatable root sampling, staining, and scoring methods. Store representative images and the number of fields examined.",
    caution:
      "Colonization percentage alone does not prove yield benefit. Interpret it with plant, soil, and treatment evidence.",
  },
  "Nutrient Cycling": {
    icon: Activity,
    title: "Biological nutrient-cycling workspace",
    description:
      "Link decomposition, microbial activity, soil fauna, plant uptake, and conventional nutrient tests in one auditable record.",
    measurements: [
      "Organic matter",
      "Respiration or activity proxy",
      "Available nutrient tests",
      "Plant tissue response",
      "Treatment-to-outcome timing",
    ],
    method:
      "Pair biology observations with standard soil chemistry and plant-response measurements rather than treating either layer alone.",
    caution:
      "AgroQ does not infer fertilizer recommendations from microscopy alone. Recommendations remain human reviewed.",
  },
  "Compost Biology": {
    icon: Beaker,
    title: "Compost biology workspace",
    description:
      "Track compost maturity, biological observations, amendment batches, application rates, and field response.",
    measurements: [
      "Batch and feedstock provenance",
      "Temperature history",
      "Moisture and odor observations",
      "Fungal and bacterial biomass",
      "Application and outcome records",
    ],
    method:
      "Keep batch-level chain of custody and compare each amendment with untreated or standard-practice controls.",
    caution:
      "Do not label a compost product safe or mature from a single dashboard metric. Follow applicable testing and handling requirements.",
  },
  "Methods & References": {
    icon: BookOpen,
    title: "Methods, evidence, and reference library",
    description:
      "Separate published concepts, project protocols, synthetic demonstration data, and field-validated evidence.",
    measurements: [
      "Soil Biology Primer reference",
      "Peer-reviewed soil microbial ecology literature",
      "AgroQ sampling SOP and version",
      "Instrument and analyst calibration",
      "Source, confidence, and limitations",
    ],
    method:
      "Every result should point to a protocol version, sample record, analyst, raw observation, and treatment-control comparison.",
    caution:
      "This module is research-informed and independent. No affiliation with or endorsement by Dr. Elaine R. Ingham is implied.",
  },
};

function scoreTone(score) {
  if (score >= 75) return "good";
  if (score >= 60) return "watch";
  return "low";
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function calculateIndex(values) {
  const ratio = values.bacteria > 0 ? values.fungi / values.bacteria : 0;
  const ratioScore = clamp(100 - Math.abs(ratio - 1.5) * 45, 0, 100);
  const fungalScore = clamp((values.fungi / 900) * 100, 0, 100);
  const protozoaScore = clamp((values.protozoa / 350) * 100, 0, 100);
  const nematodeScore = clamp((values.nematodes / 50) * 100, 0, 100);
  const mycorrhizaeScore = clamp(values.mycorrhizae, 0, 100);

  return Math.round(
    fungalScore * 0.2 +
      ratioScore * 0.25 +
      protozoaScore * 0.18 +
      nematodeScore * 0.17 +
      mycorrhizaeScore * 0.2,
  );
}

function Gauge({ value, label }) {
  return (
    <div
      className="soil-index-gauge"
      style={{ "--soil-gauge-value": `${clamp(value, 0, 100) * 3.6}deg` }}
      aria-label={`${label}: ${value} out of 100`}
    >
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  );
}

function Badge({ children, tone = "green" }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

function TrendCard({ title, unit, values, tone, summary }) {
  return (
    <article className="soil-trend-card panel">
      <div className="soil-card-heading">
        <div>
          <span>{unit}</span>
          <h3>{title}</h3>
        </div>
        <Badge tone="green">{summary}</Badge>
      </div>
      <Sparkline values={values} tone={tone} />
      <div className="soil-trend-scale">
        <span>Oldest</span>
        <span>Latest</span>
      </div>
    </article>
  );
}

function FocusPanel({ name, onBack }) {
  const focus = focusPanels[name];
  const Icon = focus.icon;

  return (
    <div className="soil-focus-layout">
      <section className="soil-focus-hero panel">
        <div className="soil-focus-icon">
          <Icon size={28} />
        </div>
        <div>
          <span className="eyebrow">Research-informed module</span>
          <h2>{focus.title}</h2>
          <p>{focus.description}</p>
        </div>
        <button className="button button-secondary" type="button" onClick={onBack}>
          Return to overview
        </button>
      </section>

      <section className="soil-focus-grid">
        <article className="panel soil-focus-card">
          <h3>Measurements captured</h3>
          <div className="soil-check-list">
            {focus.measurements.map((measurement) => (
              <div key={measurement}>
                <CheckCircle2 size={17} />
                <span>{measurement}</span>
              </div>
            ))}
          </div>
        </article>

        <article className="panel soil-focus-card">
          <h3>Method discipline</h3>
          <p>{focus.method}</p>
          <div className="soil-method-chain">
            {["Sample", "Observe", "Verify", "Compare", "Review"].map((step, index) => (
              <div key={step}>
                <span>{index + 1}</span>
                <strong>{step}</strong>
              </div>
            ))}
          </div>
        </article>

        <article className="panel soil-focus-card soil-caution-card">
          <ShieldCheck size={28} />
          <h3>Evidence boundary</h3>
          <p>{focus.caution}</p>
        </article>
      </section>
    </div>
  );
}

function ObservationModal({ onClose, onSave }) {
  const [form, setForm] = useState({
    zone: "North Control",
    method: "Direct microscopy",
    fungi: "650",
    bacteria: "500",
    protozoa: "250",
    nematodes: "30",
    mycorrhizae: "55",
    protocol: "SFW-MICRO-1.1",
    calibrationId: "CAL-MICRO-NEW",
    depthCm: "10",
    gps: "39.14021, -121.59142",
    confidence: "80",
    analyst: "Research operator",
    notes: "",
  });

  const update = (field, value) =>
    setForm((current) => ({ ...current, [field]: value }));

  const submit = (event) => {
    event.preventDefault();
    const numeric = {
      fungi: Number(form.fungi),
      bacteria: Number(form.bacteria),
      protozoa: Number(form.protozoa),
      nematodes: Number(form.nematodes),
      mycorrhizae: Number(form.mycorrhizae),
    };
    const ratio = numeric.bacteria > 0 ? numeric.fungi / numeric.bacteria : 0;

    onSave({
      id: `SFW-${Date.now()}`,
      date: new Date().toISOString().slice(0, 10),
      zone: form.zone.trim(),
      method: form.method,
      ...numeric,
      ratio: Number(ratio.toFixed(1)),
      bhi: calculateIndex(numeric),
      protocol: form.protocol.trim(),
      calibrationId: form.calibrationId.trim(),
      depthCm: Number(form.depthCm),
      gps: form.gps.trim(),
      confidence: Number(form.confidence),
      analyst: form.analyst.trim(),
      reviewStatus: "Needs review",
      notes: form.notes.trim() || "New research observation.",
    });
  };

  return (
    <div className="soil-modal-backdrop" role="presentation">
      <form className="soil-observation-modal panel" onSubmit={submit}>
        <div className="soil-modal-heading">
          <div>
            <span className="eyebrow">Manual research entry</span>
            <h2>Add soil-biology observation</h2>
          </div>
          <button
            className="icon-button"
            type="button"
            onClick={onClose}
            aria-label="Close form"
          >
            <X size={19} />
          </button>
        </div>

        <div className="soil-form-grid">
          <label>
            Plot or zone
            <input
              required
              value={form.zone}
              onChange={(event) => update("zone", event.target.value)}
            />
          </label>
          <label>
            Sampling method
            <select
              value={form.method}
              onChange={(event) => update("method", event.target.value)}
            >
              <option>Direct microscopy</option>
              <option>Root staining</option>
              <option>Compost microscopy</option>
              <option>Field observation</option>
            </select>
          </label>
          <label>
            Protocol version
            <input
              required
              value={form.protocol}
              onChange={(event) => update("protocol", event.target.value)}
            />
          </label>
          <label>
            Calibration record
            <input
              required
              value={form.calibrationId}
              onChange={(event) => update("calibrationId", event.target.value)}
            />
          </label>
          <label>
            Sample depth (cm)
            <input
              required
              min="0"
              step="1"
              type="number"
              value={form.depthCm}
              onChange={(event) => update("depthCm", event.target.value)}
            />
          </label>
          <label>
            GPS coordinates
            <input
              required
              value={form.gps}
              onChange={(event) => update("gps", event.target.value)}
            />
          </label>
          <label>
            Confidence (%)
            <input
              required
              min="0"
              max="100"
              step="1"
              type="number"
              value={form.confidence}
              onChange={(event) => update("confidence", event.target.value)}
            />
          </label>
          <label>
            Analyst
            <input
              required
              value={form.analyst}
              onChange={(event) => update("analyst", event.target.value)}
            />
          </label>
          {[
            ["fungi", "Fungal biomass"],
            ["bacteria", "Bacterial biomass"],
            ["protozoa", "Protozoa count"],
            ["nematodes", "Nematode count"],
            ["mycorrhizae", "Mycorrhizal colonization (%)"],
          ].map(([field, label]) => (
            <label key={field}>
              {label}
              <input
                required
                min="0"
                step="0.1"
                type="number"
                value={form[field]}
                onChange={(event) => update(field, event.target.value)}
              />
            </label>
          ))}
          <label className="soil-form-wide">
            Notes
            <textarea
              rows="3"
              value={form.notes}
              onChange={(event) => update("notes", event.target.value)}
              placeholder="Treatment, sample condition, analyst confidence, or follow-up."
            />
          </label>
        </div>

        <div className="soil-modal-actions">
          <button className="button button-secondary" type="button" onClick={onClose}>
            Cancel
          </button>
          <button className="button button-primary" type="submit">
            <Plus size={17} />
            Save observation
          </button>
        </div>
      </form>
    </div>
  );
}

export default function SoilBiologyPage({
  onOpenExperiments,
  onOpenOperations,
  onFreezeProblem,
  onOpenQuantum,
}) {
  const [activeTab, setActiveTab] = useState(tabs[0]);
  const [observations, setObservations] = useState(initialObservations);
  const [showObservationForm, setShowObservationForm] = useState(false);
  const [filters, setFilters] = useState({
    zone: "All plots",
    dateRange: "Last 90 days",
    compareTo: "Untreated Control",
    method: "All methods",
  });

  const zones = useMemo(
    () => ["All plots", ...new Set(observations.map((item) => item.zone))],
    [observations],
  );

  const filtered = useMemo(
    () =>
      observations.filter(
        (item) =>
          (filters.zone === "All plots" || item.zone === filters.zone) &&
          (filters.method === "All methods" || item.method === filters.method),
      ),
    [filters.method, filters.zone, observations],
  );

  const averages = useMemo(() => {
    const source = filtered.length ? filtered : observations;
    const average = (field) =>
      Math.round(
        source.reduce((sum, item) => sum + Number(item[field] || 0), 0) /
          source.length,
      );
    const averageFloat = (field) =>
      source.reduce((sum, item) => sum + Number(item[field] || 0), 0) /
      source.length;

    return {
      bhi: average("bhi"),
      fungi: average("fungi"),
      bacteria: average("bacteria"),
      protozoa: average("protozoa"),
      nematodes: average("nematodes"),
      mycorrhizae: average("mycorrhizae"),
      ratio: averageFloat("ratio").toFixed(1),
    };
  }, [filtered, observations]);

  const setFilter = (field, value) =>
    setFilters((current) => ({ ...current, [field]: value }));

  const saveObservation = (observation) => {
    setObservations((current) => [observation, ...current]);
    setShowObservationForm(false);
  };

  const exportReport = () => {
    const report = {
      module: "AgroQ Soil Biology",
      generatedAt: new Date().toISOString(),
      evidenceBoundary:
        "Research-informed prototype data. Human review and validated laboratory or agronomic testing remain required.",
      filters,
      summary: averages,
      observations: filtered,
    };
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `agroq-soil-biology-${new Date().toISOString().slice(0, 10)}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  if (activeTab !== tabs[0]) {
    return (
      <div className="page-stack soil-biology-page">
        <div className="soil-tabs" role="tablist" aria-label="Soil biology modules">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              className={activeTab === tab ? "soil-tab-active" : ""}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>
        {extendedTabs.has(activeTab) ? (
          <SoilResearchExtensions
            activeTab={activeTab}
            observations={observations}
            onFreezeProblem={onFreezeProblem}
            onOpenQuantum={onOpenQuantum}
            onBack={() => setActiveTab(tabs[0])}
          />
        ) : (
          <FocusPanel name={activeTab} onBack={() => setActiveTab(tabs[0])} />
        )}
      </div>
    );
  }

  const trendSource = [...observations].reverse();

  return (
    <div className="page-stack soil-biology-page">
      <section className="soil-page-header">
        <div>
          <span className="eyebrow">Living systems research module</span>
          <h1>Soil Biology · Soil Food Web</h1>
          <p>
            Research-informed biological observations integrated with AgroQ
            experiments, treatments, operations, and human-reviewed recommendations.
          </p>
        </div>
        <div className="soil-header-actions">
          <Badge tone="amber">Synthetic prototype data</Badge>
          <button
            className="button button-primary"
            type="button"
            onClick={() => setShowObservationForm(true)}
          >
            <Plus size={17} />
            New observation
          </button>
        </div>
      </section>

      <div className="soil-tabs" role="tablist" aria-label="Soil biology modules">
        {tabs.map((tab) => (
          <button
            key={tab}
            type="button"
            className={activeTab === tab ? "soil-tab-active" : ""}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      <section className="soil-filter-bar panel">
        <label>
          Plot or zone
          <select
            value={filters.zone}
            onChange={(event) => setFilter("zone", event.target.value)}
          >
            {zones.map((zone) => (
              <option key={zone}>{zone}</option>
            ))}
          </select>
        </label>
        <label>
          Date range
          <select
            value={filters.dateRange}
            onChange={(event) => setFilter("dateRange", event.target.value)}
          >
            <option>Last 30 days</option>
            <option>Last 90 days</option>
            <option>Current season</option>
            <option>All records</option>
          </select>
        </label>
        <label>
          Compare with
          <select
            value={filters.compareTo}
            onChange={(event) => setFilter("compareTo", event.target.value)}
          >
            {zones
              .filter((zone) => zone !== "All plots")
              .map((zone) => (
                <option key={zone}>{zone}</option>
              ))}
          </select>
        </label>
        <label>
          Sampling method
          <select
            value={filters.method}
            onChange={(event) => setFilter("method", event.target.value)}
          >
            <option>All methods</option>
            <option>Direct microscopy</option>
            <option>Root staining</option>
            <option>Compost microscopy</option>
            <option>Field observation</option>
          </select>
        </label>
        <button
          className="button button-secondary soil-export-button"
          type="button"
          onClick={exportReport}
        >
          <Download size={17} />
          Export report
        </button>
      </section>

      <section className="soil-dashboard-layout">
        <div className="soil-dashboard-main">
          <section className="soil-kpi-grid">
            <article className="panel soil-index-card">
              <div className="soil-card-heading">
                <div>
                  <span>Prototype composite</span>
                  <h3>Biological Health Index</h3>
                </div>
                <Activity size={20} />
              </div>
              <div className="soil-index-content">
                <Gauge value={averages.bhi} label={scoreTone(averages.bhi)} />
                <div className="soil-driver-list">
                  {[
                    ["Fungal biomass", averages.fungi, "µg/g"],
                    ["Bacterial biomass", averages.bacteria, "µg/g"],
                    ["Protozoa activity", averages.protozoa, "count/g"],
                    ["Nematode diversity", averages.nematodes, "count/g"],
                    ["Mycorrhizae", averages.mycorrhizae, "%"],
                  ].map(([label, value, unit]) => (
                    <div key={label}>
                      <span>{label}</span>
                      <strong>
                        {value} {unit}
                      </strong>
                    </div>
                  ))}
                </div>
              </div>
              <p className="soil-disclaimer">
                Composite demonstration score only; not a diagnostic laboratory result.
              </p>
            </article>

            <article className="panel soil-ratio-card">
              <div className="soil-card-heading">
                <div>
                  <span>Microbial balance</span>
                  <h3>Fungal : bacterial ratio</h3>
                </div>
                <Microscope size={20} />
              </div>
              <div className="soil-ratio-gauge">
                <div className="soil-ratio-arc">
                  <span
                    className="soil-ratio-needle"
                    style={{
                      "--ratio-position": `${
                        clamp(Number(averages.ratio) / 4, 0, 1) * 180 - 90
                      }deg`,
                    }}
                  />
                </div>
                <strong>{averages.ratio}</strong>
                <span>Observed average</span>
              </div>
              <div className="soil-ratio-scale">
                <span>0</span>
                <span>1</span>
                <span>2</span>
                <span>3</span>
                <span>4+</span>
              </div>
              <p className="soil-disclaimer">
                Interpret ratios by crop, ecosystem, method, treatment, and baseline.
              </p>
            </article>

            <article className="panel soil-pyramid-card">
              <div className="soil-card-heading">
                <div>
                  <span>Living network</span>
                  <h3>Soil food web pyramid</h3>
                </div>
                <Leaf size={20} />
              </div>
              <div className="soil-pyramid">
                {[
                  ["Arthropods", "Shredders and predators"],
                  ["Nematodes", "Grazers and predators"],
                  ["Protozoa", "Microbial grazers"],
                  ["Fungi", "Decomposers and symbionts"],
                  ["Bacteria", "Decomposers"],
                  ["Organic matter", "Energy and habitat"],
                ].map(([group, role], index) => (
                  <div key={group} style={{ "--pyramid-level": index }}>
                    <strong>{group}</strong>
                    <span>{role}</span>
                  </div>
                ))}
              </div>
            </article>
          </section>

          <section className="soil-trend-grid">
            <TrendCard
              title="Microbial biomass"
              unit="Fungi trend"
              values={trendSource.map((item) => item.fungi)}
              tone="#5cf1a0"
              summary="Tracked"
            />
            <TrendCard
              title="Protozoa activity"
              unit="Count per gram"
              values={trendSource.map((item) => item.protozoa)}
              tone="#80c4ff"
              summary="Observed"
            />
            <TrendCard
              title="Mycorrhizal colonization"
              unit="Percent of roots"
              values={trendSource.map((item) => item.mycorrhizae)}
              tone="#f3b96c"
              summary={`${averages.mycorrhizae}% avg`}
            />
          </section>

          <section className="panel soil-observation-table-panel">
            <div className="soil-table-heading">
              <div>
                <span className="eyebrow">Evidence ledger</span>
                <h2>Recent soil-biology observations</h2>
              </div>
              <div className="soil-table-actions">
                <Search size={17} />
                <span>{filtered.length} records</span>
              </div>
            </div>
            <div className="soil-table-scroll">
              <table className="soil-observation-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Plot / zone</th>
                    <th>Fungi</th>
                    <th>Bacteria</th>
                    <th>F:B</th>
                    <th>Protozoa</th>
                    <th>Nematodes</th>
                    <th>Mycorrhizae</th>
                    <th>BHI</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((observation) => (
                    <tr key={observation.id}>
                      <td>{observation.date}</td>
                      <td>
                        <strong>{observation.zone}</strong>
                        <small>{observation.method}</small>
                      </td>
                      <td>{observation.fungi}</td>
                      <td>{observation.bacteria}</td>
                      <td>{observation.ratio}</td>
                      <td>{observation.protozoa}</td>
                      <td>{observation.nematodes}</td>
                      <td>{observation.mycorrhizae}%</td>
                      <td>
                        <Badge
                          tone={
                            observation.bhi >= 75
                              ? "green"
                              : observation.bhi >= 60
                                ? "amber"
                                : "red"
                          }
                        >
                          {observation.bhi}
                        </Badge>
                      </td>
                      <td>{observation.notes}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="soil-principles-strip panel">
            {[
              [BookOpen, "Evidence based", "Protocol and source recorded"],
              [Leaf, "Living systems", "Whole food-web context"],
              [ShieldCheck, "Human supervised", "No automatic field actuation"],
              [TestTube2, "Compare and learn", "Controls versus treatments"],
            ].map(([Icon, title, copy]) => (
              <div key={title}>
                <Icon size={20} />
                <span>
                  <strong>{title}</strong>
                  <small>{copy}</small>
                </span>
              </div>
            ))}
          </section>
        </div>

        <aside className="soil-dashboard-aside">
          <article className="panel soil-research-card">
            <div className="soil-research-title">
              <Leaf size={20} />
              <div>
                <span>Research foundation</span>
                <strong>Dr. Elaine R. Ingham</strong>
              </div>
            </div>
            <p>
              This module translates soil-food-web concepts into traceable
              observations, experiments, treatment comparisons, and human-reviewed
              decisions.
            </p>
            <div className="soil-research-boundary">
              Independent, research-informed prototype. No affiliation or endorsement
              is implied.
            </div>
            <button
              className="text-button"
              type="button"
              onClick={() => setActiveTab("Methods & References")}
            >
              View methods and references
              <ChevronRight size={16} />
            </button>
          </article>

          <article className="panel soil-side-card">
            <div className="soil-side-heading">
              <ClipboardList size={19} />
              <h3>Recent observations</h3>
            </div>
            <div className="soil-mini-observations">
              {observations.slice(0, 4).map((observation) => (
                <div key={observation.id}>
                  <span>
                    <strong>{observation.zone}</strong>
                    <small>{observation.date}</small>
                  </span>
                  <Badge
                    tone={
                      observation.bhi >= 75
                        ? "green"
                        : observation.bhi >= 60
                          ? "amber"
                          : "red"
                    }
                  >
                    {observation.bhi}
                  </Badge>
                </div>
              ))}
            </div>
            <button
              className="button button-secondary full-width"
              type="button"
              onClick={() => setShowObservationForm(true)}
            >
              Add observation
            </button>
          </article>

          <article className="panel soil-side-card">
            <div className="soil-side-heading">
              <CheckCircle2 size={19} />
              <h3>Upcoming soil-biology tasks</h3>
            </div>
            <div className="soil-task-list">
              {soilTasks.map(([task, date, type]) => (
                <div key={task}>
                  <span className="soil-task-icon">
                    <ClipboardList size={15} />
                  </span>
                  <span>
                    <strong>{task}</strong>
                    <small>
                      {date} · {type}
                    </small>
                  </span>
                </div>
              ))}
            </div>
            <button
              className="button button-secondary full-width"
              type="button"
              onClick={onOpenOperations}
            >
              Open operations
            </button>
          </article>

          <article className="panel soil-side-card soil-experiment-link">
            <TestTube2 size={28} />
            <h3>Link biology to experiments</h3>
            <p>
              Compare compost, beneficial, cover-crop, and untreated plots using the
              same sampling budget.
            </p>
            <button
              className="button button-primary full-width"
              type="button"
              onClick={onOpenExperiments}
            >
              Open experiments
              <ChevronRight size={17} />
            </button>
          </article>
        </aside>
      </section>

      {showObservationForm && (
        <ObservationModal
          onClose={() => setShowObservationForm(false)}
          onSave={saveObservation}
        />
      )}
    </div>
  );
}
