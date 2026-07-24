# AgroQ Build Log — Day 1

## Focus

Founder administration, controlled access, biological sequence evidence, and a
three-experiment demonstration portfolio.

## Work completed

### Founder administrator identity

- Configured the existing `admin` account as the active founder administrator.
- Updated the display identity to **Othon Reyes Jr.**
- Added the administrator email and founder profile information.
- Preserved role separation: the authorization role is `administrator`; public
  relationship categories remain separate.
- Replaced the account password through a hidden terminal prompt.
- Verified that passwords remain one-way hashed.

### Access and community foundation

- Added public access-request and invitation workflows.
- Preserved strict role restrictions for public invitations.
- Kept administrator creation unavailable through public invitation codes.
- Added founder profile, access administration, beta, investor, contributor,
  partner, researcher, and customer relationship pathways.
- Added temporary administrator magic-link readiness and audit history.

### DNA and protein sequence workspace

- Added administrator and researcher sequence search.
- Connected the application to NCBI public sequence records.
- Added DNA/RNA and protein search modes.
- Added one-click sequence retrieval, validation, insertion, and experiment linking.
- Added FASTA parsing and sequence measurements.
- Added nucleotide GC percentage and ambiguity counts.
- Added protein sequence length and ambiguity counts.
- Added SHA-256 checksums and source provenance.
- Added FASTA, JSON, and CSV exports.
- Added explicit scientific claim boundaries: database association is not causality.

### Three demonstration experiments

1. **Slobolt Lettuce Low-Water Biomass-Retention Phenotype**
   - Synthetic treatment and control groups
   - Fresh shoot biomass
   - Canopy area
   - Leaf count
   - Wilting score
   - Root-zone moisture
   - Human approval workflow

2. **Slobolt Lettuce Heat-Resilience and Bolting-Delay Phenotype**
   - Synthetic warm-condition group
   - Synthetic baseline control
   - Bolting-delay score
   - Canopy retention
   - Biomass comparison
   - Administrator approval gate

3. **Lettuce Candidate Sequence-to-Pigmentation Evidence Map**
   - Public DNA/protein evidence search
   - Accession provenance
   - Sequence checksums
   - Experiment linking
   - Human interpretation
   - Exportable evidence packet

## Validation evidence

```text
Focused bioinformatics tests: 8 passed
Full backend suite after Day 1: 109 passed
Professional frontend build: passed
Vite modules transformed: 2,532
Production bundle generated successfully
```

## Demonstrated workflow

```text
Administrator sign-in
        ↓
Choose DNA/RNA or protein search
        ↓
Search public records
        ↓
Insert and preserve provenance
        ↓
Link record to an experiment
        ↓
Review interpretation and limitations
        ↓
Export FASTA, JSON, or CSV
```

## Claim boundary

The software demonstrates controlled experiment records and evidence management. It
does not claim that a new plant variety has been created, that a public sequence causes
a phenotype, or that field performance has been validated.
