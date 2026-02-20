# AWS Secrets Manager Vault

Inventory and classify all AWS Secrets Manager secrets across 4 BrightHive AWS accounts.

## Features

- **Multi-account enumeration** - Fetches secrets from DEV, STAGE, PROD, and MAIN AWS accounts
- **Automatic classification** - Categorizes secrets by type (DB password, API key, SSH key, token, connection string, etc.)
- **Indexed output** - Generates searchable JSON index and markdown documentation
- **Alias mapping** - Quick lookup by name, type, and account

## Quick Start

```bash
cd aws-secrets-vault

# List all secrets across all accounts
./cli/secrets list

# Classify and index all secrets
./cli/secrets classify

# Export to JSON index
./cli/secrets export

# Organize by classification
./cli/secrets organize --materialize
```

## Directory Structure

```
aws-secrets-vault/
├── cli/
│   └── secrets              # Main CLI tool
├── lib/
│   ├── classifier.py       # Secret classification logic
│   ├── indexer.py          # Index building and export
│   ├── models.py           # Data models (Secret, Classification)
│   ├── aws_client.py       # AWS Secrets Manager client
│   └── config.py           # Account configuration
├── data/
│   ├── index.json          # Generated: searchable index
│   ├── index.md            # Generated: markdown documentation
│   ├── aliases.json        # Generated: lookup tables
│   ├── organized/          # Generated: organized by type
│   │   ├── database_passwords/
│   │   ├── api_keys/
│   │   ├── connection_strings/
│   │   └── ...
│   └── exports/            # Generated: raw exports
├── tests/
│   └── unit/
│       ├── test_classifier.py
│       ├── test_indexer.py
│       ├── test_aws_client.py
│       └── test_models.py
└── README.md               # This file
```

## Classification Types

Secrets are automatically classified into:

- `database_password` - DB user passwords (Redshift, RDS, etc.)
- `api_key` - API keys and tokens
- `ssh_key` - SSH private keys
- `connection_string` - Database/service connection strings
- `oauth_token` - OAuth and JWT tokens
- `webhook_secret` - Webhook signing secrets
- `encryption_key` - Encryption/signing keys
- `certificate` - SSL/TLS certificates
- `credentials_json` - JSON credential files
- `unknown` - Could not be classified

## Output Files

### `index.json`
Searchable JSON with all secrets and classifications:
```json
{
  "secrets": [
    {
      "name": "redshift/admin-password",
      "account_id": "531731217746",
      "account_name": "DEV",
      "type": "database_password",
      "confidence": 0.95,
      "created_at": "2025-01-15",
      "last_updated": "2025-02-16"
    }
  ],
  "summary": {
    "total_secrets": 42,
    "by_type": {...},
    "by_account": {...}
  }
}
```

### `aliases.json`
Fast lookup by name, type, account:
```json
{
  "by_name": {"secret_name": ["DEV", "secret_object"]},
  "by_type": {"database_password": [...]},
  "by_account": {"531717346": [...]}
}
```

### `organized/` directory
Secrets organized by classification type:
```
organized/
├── database_passwords/
│   ├── redshift_admin_password.json
│   └── rds_dev_credentials.json
├── api_keys/
│   ├── openmetadata_token.json
│   └── github_key.json
└── ...
```

## Commands

### list
List all secrets with basic info:
```bash
./cli/secrets list [--account DEV|STAGE|PROD|MAIN] [--type database_password]
```

### classify
Fetch and classify all secrets:
```bash
./cli/secrets classify [--account DEV|STAGE|PROD|MAIN]
```

### export
Export secrets to JSON index:
```bash
./cli/secrets export [--output data/index.json]
```

### organize
Organize classified secrets into directories:
```bash
./cli/secrets organize --materialize
```

## AWS Account Configuration

Accounts are configured in `lib/config.py`:

```python
AWS_ACCOUNTS = {
    "DEV": "531731217746",
    "STAGE": "873769991712",
    "PROD": "104403016368",
    "MAIN": "396527728813",
}
```

## Authentication

Requires AWS CLI configured with appropriate profiles:

```bash
# Configure each account
aws configure --profile brighthive-dev
aws configure --profile brighthive-stage
aws configure --profile brighthive-prod
aws configure --profile brighthive-main

# Or use environment variables
export AWS_PROFILE=brighthive-dev
```

## Testing

```bash
# Run all tests
python -m pytest tests/unit -v

# Test specific module
python -m pytest tests/unit/test_classifier.py -v

# Test with coverage
python -m pytest tests/unit -v --cov=lib
```

## Usage Examples

### Get all database passwords
```bash
./cli/secrets list --type database_password
```

### Export secrets from PROD account only
```bash
./cli/secrets export --account PROD --output data/exports/prod_secrets.json
```

### Find a specific secret
```bash
./cli/secrets list --grep "redshift"
```

### Generate markdown documentation
```bash
./cli/secrets export --format markdown > data/SECRETS_INVENTORY.md
```

## Safety Features

- ✅ **Read-only by default** - Never modifies secrets
- ✅ **Classification only** - Secrets are never stored in plaintext
- ✅ **Local caching** - Index cached in `/data/` (add to .gitignore)
- ✅ **Audit trail** - All operations logged

## Integration

Use the classifier in your code:

```python
from lib.classifier import SecretClassifier
from lib.aws_client import AWSSecretsManager

client = AWSSecretsManager(account_id="531731217746", region="us-east-1")
classifier = SecretClassifier()

secrets = client.list_all_secrets()
for secret in secrets:
    classification = classifier.classify(secret)
    print(f"{secret['Name']}: {classification['type']}")
```

## Troubleshooting

### No secrets found
- Verify AWS CLI profiles are configured: `aws configure list`
- Check IAM permissions: `aws secretsmanager list-secrets --profile brighthive-dev`
- Verify region: Secrets Manager secrets can be region-specific

### Classification incorrect
- Check `lib/classifier.py` patterns
- Add test case to `tests/unit/test_classifier.py`
- Update classification logic

### Slow performance
- Secrets are cached locally, first run is slowest
- Use `--account` flag to limit to one account
- Consider parallel fetching (see `lib/aws_client.py`)

## References

- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [LastPass Vault Tool](../lastpass-vault/) - Similar pattern for LastPass
- [BrightHive AWS Architecture](../../ARCHITECTURE.md)
