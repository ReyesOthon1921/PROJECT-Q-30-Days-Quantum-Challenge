# Phase 51 external dataset

Copy `phase51_external_dataset_template.csv` to
`phase51_external_dataset.csv`, then populate it with a newly declared,
independent RNA dataset.

Rules:

- Do not reuse any Phase 49 or Phase 50 sequence.
- Use RNA letters `A`, `U`, `G`, and `C` only.
- Use pseudoknot-free dot-bracket notation containing only `.`, `(`, and `)`.
- Keep the sequence and reference structure the same length.
- Use `external_test` in the `split` column for every row.
- Preserve source record IDs, source URLs, and the reference method.
- Do not run the Phase 51 comparison until the dataset audit passes and the
  dataset checksum is committed.

The template is intentionally empty. Verification uses a separate generated
fixture and does not declare research data.
