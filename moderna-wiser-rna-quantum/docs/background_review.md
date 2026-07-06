\# Background Review



\## Biological Problem



mRNA secondary structure prediction asks how an RNA sequence made of A, U, C, and G folds into paired and unpaired regions.



Secondary structure can affect molecular stability, translation efficiency, and manufacturability.



\## Classical Benchmark



ViennaRNA will be used as the classical benchmark.



For each RNA sequence, ViennaRNA can return:



\- MFE structure

\- MFE energy

\- dot-bracket notation

\- candidate structure energy evaluation



\## Dot-Bracket Notation



Dot-bracket notation represents RNA secondary structure using simple characters:



\- `.` means unpaired nucleotide

\- `(` means left side of a base pair

\- `)` means right side of a base pair



Example:



```text

sequence:  GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG

structure: .................(((....))).................

