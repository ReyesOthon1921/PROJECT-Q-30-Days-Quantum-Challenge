# Final Deployment Checklist — Phase 47

## Local Test

Run:

```cmd
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

Test API:

```text
http://127.0.0.1:5000/api/exact-validation-dashboard
```

Expected:

```text
"success": true
```

## GitHub Check

Run:

```cmd
git log --oneline -5
git status --short
```

Only the unrelated Quantum-Communication-Dashboard files should remain modified.

## Render Deploy

1. Open Render.
2. Open `moderna-wiser-rna-quantum` service.
3. Click `Manual Deploy`.
4. Click `Deploy latest commit`.
5. Wait until deploy finishes.
6. Open the live dashboard.
7. Hard refresh with `CTRL + F5`.

Live dashboard:

https://moderna-wiser-rna-quantum.onrender.com

Live API test:

https://moderna-wiser-rna-quantum.onrender.com/api/exact-validation-dashboard

## Safe Final Status

After deployment, the prototype package is complete for professor review.
