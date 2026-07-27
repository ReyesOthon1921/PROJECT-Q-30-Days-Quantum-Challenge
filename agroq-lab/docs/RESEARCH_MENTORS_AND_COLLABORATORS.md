# Research Mentors & Collaborators

## Misbahul Islam

**Website role:** Research Mentor & Publication Collaborator

**Areas of contribution:** Bioinformatics validation, RNA optimization methodology, QUBO research design, quantum benchmarking, and publication planning.

Misbahul Islam reached out during the early development of the RNAQ project and offered research mentorship, methodological guidance, and support toward developing the work into a publication. At the time, Othon Reyes Jr. was beginning his work in quantum computing and computational bioinformatics, and this guidance helped direct the project from an early software prototype toward a structured research study.

He recommended organizing the work around a defined research problem, literature review, research-gap analysis, measurable objectives, dataset development, bioinformatics preprocessing, QUBO formulation, classical and quantum benchmarking, qubit-compression research, and publication-ready validation. He also encouraged the use of BLAST and RCSB PDB resources to strengthen the biological and structural validation process.

The collaboration established a clear division of responsibility: Othon Reyes Jr. continues developing the software, conducting the experiments, and producing the research data, while Misbahul Islam helps review the methodology, verify the results, and support the preparation of a research paper for submission to an appropriate journal.

Othon Reyes Jr. remains grateful to the mentors, researchers, educators, and collaborators who offered their time and knowledge while he was entering this field. Their guidance strengthened the scientific direction of the project while he continued developing his own capabilities as a researcher and software developer.

## Role boundary

This acknowledgment does not identify Misbahul Islam as a co-founder, project owner, principal investigator, or formally appointed faculty adviser. Publication authorship will be determined separately during manuscript development through an explicit contribution and authorship agreement.

## Collaboration pathway

```mermaid
flowchart TD
    A["RNAQ Initial Prototype<br/>Othon Reyes Jr."] --> B["Mentorship Outreach<br/>Misbahul Islam"]

    B --> C["Research Problem Definition"]
    C --> D["Literature Review<br/>RNA Folding · QUBO · Quantum Algorithms · QRAC/QRAO"]
    D --> E["Research-Gap Identification"]
    E --> F["Research Objectives"]

    F --> G["Dataset Collection"]
    G --> G1["RNA Sequences"]
    G --> G2["Secondary-Structure Datasets"]
    G --> G3["BLAST Sequence Validation"]
    G --> G4["RCSB PDB Structural Data"]

    G --> H["Bioinformatics Preprocessing"]
    H --> H1["Sequence Cleaning"]
    H --> H2["Feature Extraction"]
    H --> H3["Base-Pair and Stem Generation"]
    H --> H4["Energy Calculations"]
    H --> H5["Constraint Generation"]

    H --> I["QUBO Formulation"]
    I --> I1["Decision Variables"]
    I --> I2["Objective Function"]
    I --> I3["Penalty Constraints"]
    I --> I4["Hamiltonian Generation"]

    I --> J["Solver Experiments"]
    J --> J1["Exact Enumeration"]
    J --> J2["Greedy Optimization"]
    J --> J3["Simulated Annealing"]
    J --> J4["QAOA"]
    J --> J5["VQE"]

    J --> K["Equal-Budget Benchmarking"]
    K --> L["Variable and Qubit Compression"]
    L --> M["QRAC / QRAO Investigation"]
    M --> N["Hardware-Readiness Analysis"]
    N --> O["Reproducible Results and Dataset"]

    O --> P["Joint Methodology and Results Verification"]
    P --> Q["Research Paper Development"]
    Q --> R["Journal Submission"]
```

## Role assignment

```mermaid
flowchart LR
    subgraph OR["Othon Reyes Jr.<br/>Founder · Researcher · Lead Developer"]
        O1["Design and build the RNAQ platform"]
        O2["Implement the bioinformatics and QUBO pipeline"]
        O3["Run classical and quantum experiments"]
        O4["Generate datasets, benchmarks, graphs, and reports"]
        O5["Document reproducible results"]
    end

    subgraph MI["Misbahul Islam<br/>Research Mentor · Publication Collaborator"]
        M1["Help frame the research problem"]
        M2["Recommend BLAST and RCSB validation"]
        M3["Guide literature-review and research-gap analysis"]
        M4["Review research methodology and results"]
        M5["Support manuscript organization and journal preparation"]
    end

    O1 --> S["Shared Research Collaboration"]
    O2 --> S
    O3 --> S
    O4 --> S
    O5 --> S

    M1 --> S
    M2 --> S
    M3 --> S
    M4 --> S
    M5 --> S

    S --> V["Verify Evidence and Interpret Findings"]
    V --> P["Prepare Publication Manuscript"]
    P --> J["Submit to an Appropriate Journal"]
```
