# RNAQ Labs 3-Minute MVP Demo Packet

## Demo label
day24_challenge_demo

## Audience mode
challenge

## Input sequence
`GGGAAAUCC`

## Fast results
- Sequence length: 9
- GC content: 55.56%
- Candidate base pairs: 9
- Candidate stems: 4
- QUBO variables: 4
- QUBO conflict edges: 6
- Graph density: 1.0
- Connected components: 1
- Max degree: 3
- Hub variables: 4
- Graph risk label: High graph risk

## Recommended solver path
Run exact validation first, then compare greedy and simulated annealing.

## 3-minute story
1. Challenge goal: show a reproducible classical-to-quantum RNA optimization workflow.
2. Input: paste an RNA sequence or choose a sample sequence.
3. Pipeline: candidate stems become QUBO variables; conflicts become graph edges.
4. Output: report the solver path, graph risk, validation status, and next quantum-readiness step.

## Safe claim
This MVP is a computational benchmark and decision-intelligence prototype. It does not claim quantum advantage, clinical accuracy, or final biological validation.

## Next milestone
Connect this guided demo panel to the full Flask dashboard and route each metric to the existing strict classical, exact-validation, graph-diagnostic, and quantum-readiness outputs.
