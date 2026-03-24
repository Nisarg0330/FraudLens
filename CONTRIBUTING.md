# Contributing to FraudLens

## Team

| Member | Role | Owns |
|--------|------|------|
| **Nisarg** | Backend & ML Engineer | `/backend`, `/ml`, `/simulator`, `/infra` |
| **Deep** | Frontend & UX Engineer | `/frontend` |

## Branch Strategy

- `main` — Production-ready. Protected. Merge only via release PR from `develop`.
- `develop` — Integration branch. All feature branches merge here.
- `feature/*` — Short-lived task branches (1–3 days).

## Commit Convention
```
feat(scope): add scoring endpoint
fix(scope): fix WebSocket reconnection
refactor(scope): simplify feature pipeline
docs: update API contract
test(scope): add unit tests for alerts
chore: update Docker config
```

## Pull Request Rules

1. Always PR into `develop` (never directly into `main`)
2. Require 1 reviewer approval
3. CI must pass (linting + tests)
4. Squash and merge to keep history clean
5. Delete feature branch after merge

## API Contract

The API contract at `/docs/api-contract.md` is the source of truth.
**Any API change must update the contract FIRST** as part of the same PR.