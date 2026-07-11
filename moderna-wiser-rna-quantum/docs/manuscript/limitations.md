# 6. Limitations

This project is a prototype benchmark and feasibility framework.

The project does not claim:

- quantum advantage,
- clinical accuracy,
- production RNA design readiness,
- final biological validation,
- proven QUBO novelty before literature comparison,
- proven compression improvement before rounded-solution validation.

Exact enumeration is only practical for small QUBO instances because the number of assignments grows exponentially.

The current energy model is simplified and does not fully replace thermodynamic RNA folding models.

The QAOA and VQE layers are feasibility/proxy layers and should not be interpreted as evidence of quantum advantage.

The graph-aware QRAO layer validates mapping logic, but future work must test rounded compressed solutions against exact optima and biological reference structures.

The RNAfold, BLAST, and RCSB validation plans are not complete until the external outputs are collected and recorded.
