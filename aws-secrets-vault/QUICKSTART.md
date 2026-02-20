# AWS Secrets Vault - Quick Start

Built fresh! Multi-account AWS Secrets Manager classifier & inventory tool.

## What This Does

- **Fetches all secrets** from 4 AWS accounts (DEV, STAGE, PROD, MAIN)
- **Classifies each secret** automatically (DB password, API key, SSH key, certificate, etc.)
- **Indexes & organizes** for easy lookup and auditing
- **Generates reports** in JSON and Markdown

## Quick Commands

```bash
cd /Users/bado/iccha/brighthive/agentic-project-mgmt/aws-secrets-vault

# List all secrets across all accounts
./cli/secrets list

# List secrets from one account
./cli/secrets list --account DEV

# Classify and index all secrets (fetches from AWS)
./cli/secrets classify

# Organize classified secrets into directories
./cli/secrets organize --materialize

# Export to JSON
./cli/secrets export

# View generated index
cat data/index.json
cat data/index.md
ls -la data/organized/
```

## Generated Files

After running `classify` + `organize --materialize`:

- **`data/index.json`** - Complete searchable index
- **`data/index.md`** - Markdown documentation
- **`data/aliases.json`** - Fast lookup tables
- **`data/organized/`** - Secrets organized by type:
  - `database_passwords/`
  - `api_keys/`
  - `ssh_keys/`
  - `certificates/`
  - `connection_strings/`
  - `oauth_tokens/`
  - etc.

## Classification Types

- `database_password` - DB credentials (Redshift, RDS, etc.)
- `api_key` - API keys and tokens
- `ssh_key` - SSH private keys (PEM format)
- `connection_string` - Service connection strings
- `oauth_token` - OAuth/JWT tokens
- `webhook_secret` - Webhook signing secrets
- `encryption_key` - Encryption/signing keys
- `certificate` - SSL/TLS certificates
- `credentials_json` - JSON credential files
- `unknown` - Could not classify

## AWS Setup

Requires AWS CLI profiles configured for each account:

```bash
# Configure each account
aws configure --profile brighthive-dev    # 531731217746
aws configure --profile brighthive-stage  # 873769991712
aws configure --profile brighthive-prod   # 104403016368
aws configure --profile brighthive-main   # 396527728813
```

Or set profile names in `lib/config.py`:

```python
AWS_PROFILES = {
    "DEV": "my-dev-profile",
    "STAGE": "my-stage-profile",
    # etc.
}
```

## Testing

```bash
# Run classifier tests
python3 tests/unit/test_classifier.py

# Or with pytest
pytest tests/unit/ -v
```

## How It Works

1. **List Step**: For each AWS account, list all secret names
2. **Fetch Step**: Get metadata for each secret (created date, description, etc.)
3. **Classify Step**: Use pattern matching on secret names and content to classify
4. **Index Step**: Build searchable JSON index and markdown documentation
5. **Organize Step**: Write secrets to disk organized by classification type

## Example Usage

```python
from lib.aws_client import AWSSecretsManager
from lib.classifier import SecretClassifier

# Fetch from DEV account
client = AWSSecretsManager("DEV")
secrets = client.fetch_all_secrets()

# Classify each
classifier = SecretClassifier()
for secret in secrets:
    value = client.get_secret_value(secret.name)
    secret.classification = classifier.classify(secret.name, value)

# Print summary
from collections import Counter
types = Counter(s.classification.secret_type.value for s in secrets)
print(types)
```

## Files & Structure

```
aws-secrets-vault/
├── README.md              # Full documentation
├── QUICKSTART.md          # This file
├── .gitignore             # Git ignore rules
│
├── cli/
│   └── secrets            # Main CLI tool (executable)
│
├── lib/
│   ├── __init__.py        # Package exports
│   ├── config.py          # AWS account configuration
│   ├── models.py          # Data classes (Secret, Classification)
│   ├── classifier.py      # Classification logic
│   ├── aws_client.py      # AWS Secrets Manager client
│   └── indexer.py         # Index building and export
│
├── data/                  # Generated output (not in git)
│   ├── index.json
│   ├── index.md
│   ├── aliases.json
│   └── organized/
│
└── tests/
    └── unit/
        └── test_classifier.py
```

## Next Steps

1. Configure AWS CLI profiles
2. Run `./cli/secrets list` to verify access
3. Run `./cli/secrets classify` to fetch and classify all secrets
4. Check `data/index.md` for summary
5. Explore `data/organized/` for secrets by type

## Notes

- All secret values are classified but **never stored** in plaintext
- Classification is **local** - no data sent to external services
- **Always** use `.gitignore` to prevent committing secret metadata
- For automated inventory updates, add to cron or CI/CD pipeline

---

**Built for**: BrightHive multi-account AWS management
**Pattern based on**: LastPass vault classifier (sibling in agentic-project-mgmt)
**Last updated**: 2026-02-16
