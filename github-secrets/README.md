# GitHub Actions Secrets Inventory

Companion to `aws-secrets-vault/`. Inventories GitHub Actions secret **names +
last-updated timestamps** across BrightHive repos for drift detection and audit.

## The hard constraint: GitHub secrets are write-only

GitHub Actions secrets cannot be read back — the API (and `gh`) expose only the
secret **name** and **last-updated timestamp**, never the value. This is a
GitHub security guarantee, not a tooling limit. Therefore:

- This tool **inventories** names/timestamps and **detects drift** (added /
  removed / rotated). It cannot fetch values.
- The **AWS Secrets Manager vault** (`../aws-secrets-vault/`) remains the source
  of truth for secret **values**.
- Pushing a value *into* GitHub (`gh secret set`, sourced from the vault) is a
  separate, deliberate operation — intentionally not automated here.

## Usage

```bash
# List one repo's secret names + timestamps
./cli/gh-secrets list --repo brighthive/brightbot

# Inventory all brighthive repos -> data/index.json
./cli/gh-secrets inventory

# Inventory specific repos
./cli/gh-secrets inventory --repos brightbot,brighthive-webapp

# Drift vs the last inventory (added/removed/rotated names)
./cli/gh-secrets diff --repo brighthive/brightbot
```

Requires the `gh` CLI authenticated with repo admin (secrets list needs admin).

## Layout

```
github-secrets/
├── cli/gh-secrets        # CLI entrypoint
├── lib/inventory.py      # gh secret list wrapper + diff logic
└── data/index.json       # generated inventory (gitignored)
```

## Source-of-truth flow

1. **Vault is source of truth** — secret *values* live in AWS Secrets Manager,
   captured/snapshotted in `../aws-secrets-vault/`.
2. **Push to cloud** — `gh secret set NAME --repo … < value` writes a value into
   GitHub (manual, deliberate; not done by this tool).
3. **Fetch + confirm** — this tool's `inventory` / `diff` confirms the secret
   *exists* and *when it was last updated* (the only readable signal), so you can
   verify a push landed and catch out-of-band rotations.
