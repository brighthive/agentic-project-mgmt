# LastPass Vault

Minimal CLI for managing LastPass secrets locally.

## Commands

```bash
# Fetch secret value
./cli/secrets fetch <name> [field]     # field: password, username, url

# Search secrets
./cli/secrets search <query>
./cli/secrets find <query>             # alias for search

# Show full details
./cli/secrets describe <name>

# Show status
./cli/secrets status

# Sync from LastPass
./cli/secrets sync

# Delete from catalog
./cli/secrets delete <name>
```

## Examples

```bash
# Get password
./cli/secrets fetch "notion" password

# Search
./cli/secrets search neo4j

# Show details
./cli/secrets describe "BH Dev - Demo Env"

# Status
./cli/secrets status
```

## Data Location

- `data/catalog.json` - All secrets
- `data/index.json` - Metadata index
- `data/organized/` - Normalized metadata files
