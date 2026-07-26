# AgroQ Controlled-Beta Architecture and Limitations

## Architecture

```text
Public access and beta forms
        ↓
Access-request and reservation records
        ↓
Controlled contact ledger
        ↓
User interviews and pilot discovery
        ↓
Staging candidate and acceptance checks
        ↓
Persistence sentinels and verified evidence
        ↓
Claims register and YC update snapshot
        ↓
Administrator staging acceptance
```

## Current limitations

- Controlled beta is not production.
- Remote deployment remains an explicit operator action.
- SQLite requires one application worker.
- Configured paths do not prove provider-level persistence.
- Physical field integration remains blocked by its separate verified-field gate.
- Quantum results are simulator or research evidence unless hardware evidence is recorded.
- No quantum-advantage claim is authorized.
- No automated equipment action is authorized by Q17-Q19.
- User interviews and pilot discovery do not promise participation.
- Staging acceptance does not automatically promote production.
