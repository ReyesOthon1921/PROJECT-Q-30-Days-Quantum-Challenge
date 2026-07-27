# AgroQ Investor Prototype — Phases 3–6

Professional React + Three.js investor interface for the AgroQ Quantum-AI
Living Systems Lab.

## Included prototype lanes

- Phase 3: interactive 3D acre, virtual devices, digital-twin detail
- Phase 4: rules, forecasts, anomaly and recommendation previews
- Phase 5: spatial graph, Laplacian-score framing, active sampling
- Phase 6: QUBO and quantum-simulator research workspace
- Manual operations, experiments, recommendations, evidence, system status
- Synthetic scenario modes: baseline, drought, drift, pest pressure, outage
- Existing Flask backend probe with synthetic fallback

## Local run

```bat
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

Keep the existing Flask AgroQ app running at:

```text
http://127.0.0.1:5000
```

Vite proxies `/api` to Flask during local development.

## Build

```bat
npm run build
```

## Truth boundary

This package is an investor and beta-preparation prototype.

Synthetic data can demonstrate workflows, user experience, digital-twin
concepts, analytics, graph intelligence, optimization, and quantum-simulator
research. It is not genuine field validation, hardware validation, agronomic
efficacy evidence, or a quantum-advantage claim.
