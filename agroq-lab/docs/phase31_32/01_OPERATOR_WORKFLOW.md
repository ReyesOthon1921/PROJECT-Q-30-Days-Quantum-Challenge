# Admin & Sequence Lab Operator Workflow

## Configure the founder account while preserving the current password

```bat
python scripts\configure_founder_admin.py --username admin --display-name "Othon Reyes Jr." --email reyesothon1921@gmail.com --keep-password
```

## Start the services

Backend:

```bat
cd agroq-lab
python app.py
```

Frontend:

```bat
cd agroq-lab\investor-ui
npm run dev
```

## Sequence workflow

1. Sign in through the Flask login page.
2. Open the React frontend.
3. Select **Admin & Sequence Lab**.
4. Choose DNA/RNA or protein.
5. Enter a gene, protein, organism, or accession.
6. Press **Search**.
7. Select the experiment.
8. Press **Insert & link**.
9. Review the saved library.
10. Export FASTA, JSON, or CSV.

Recommended demonstration searches:

```text
Lactuca sativa pigmentation
Lactuca sativa anthocyanin
Lactuca sativa heat stress
Lactuca sativa drought response
```

A public database match is an evidence candidate, not proof of phenotype causality.
