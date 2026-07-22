# System Architecture

```text
Manual Field Work ───────────────┐
Manual Measurements ─────────────┤
Laboratory Results ──────────────┤
Sensor Adapters ─────────────────┤
Image Imports ───────────────────┘
                ↓
Local Validation and Quality Flags
                ↓
Local Gateway API
                ↓
SQLite for prototype / PostgreSQL later
                ↓
Registry + Time Series + Audit + Files
                ↓
Rules and Classical Baselines
                ↓
AI / Graph / Optimization Adapters
                ↓
Human Approval
                ↓
Action and Outcome Record
                ↓
Research Export and Reproducibility Package
```

## Deployment profiles

### Laptop prototype

- Flask application
- SQLite
- Browser interface
- Manual import/export

### Field gateway

- Small Linux computer
- Local Wi-Fi access point
- Containerized application
- PostgreSQL or durable local database
- Local object storage
- Scheduled encrypted backup

### Connected research environment

- Secure synchronization
- Central research database
- Model training service
- GIS and object storage
- Quantum-service adapters
- Read-only stakeholder dashboard

## Adapter principle

The core application communicates with integrations through versioned interfaces:

```python
class ObservationSource:
    def health(self): ...
    def fetch(self, since): ...
    def normalize(self, raw): ...
```

No vendor-specific payload should become the core data model.
