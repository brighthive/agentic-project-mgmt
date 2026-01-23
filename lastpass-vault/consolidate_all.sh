#!/bin/bash
# Consolidate all LastPass tooling into lastpass-vault
# Moves old directories into legacy/archive locations

set -e

VAULT_DIR="/Users/bado/iccha/brighthive/lastpass-vault"
BACKUP_DIR="/Users/bado/iccha/brighthive/lastpass-secrets-backup"
REFERENCE_DIR="/Users/bado/iccha/brighthive/lastpass-reference-scripts"
LEGACY_DIR="$VAULT_DIR/data/legacy"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║    CONSOLIDATING ALL LASTPASS TOOLING                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Create legacy directory structure
mkdir -p "$LEGACY_DIR/backups"
mkdir -p "$LEGACY_DIR/reference"

# Move backup exports if they exist
if [ -d "$BACKUP_DIR/exports" ]; then
    echo "📦 Archiving backup exports..."
    cp -r "$BACKUP_DIR/exports" "$LEGACY_DIR/backups/" 2>/dev/null || true
    echo "✅ Backup exports archived to: $LEGACY_DIR/backups/exports"
fi

if [ -d "$BACKUP_DIR/complete_exports" ]; then
    echo "📦 Archiving complete exports..."
    cp -r "$BACKUP_DIR/complete_exports" "$LEGACY_DIR/backups/" 2>/dev/null || true
    echo "✅ Complete exports archived"
fi

if [ -d "$BACKUP_DIR/manual_entries" ]; then
    echo "📦 Archiving manual entries..."
    cp -r "$BACKUP_DIR/manual_entries" "$LEGACY_DIR/backups/" 2>/dev/null || true
    echo "✅ Manual entries archived"
fi

# Move reference scripts
if [ -d "$REFERENCE_DIR" ]; then
    echo "📦 Archiving reference scripts..."
    cp -r "$REFERENCE_DIR"/* "$LEGACY_DIR/reference/" 2>/dev/null || true
    echo "✅ Reference scripts archived to: $LEGACY_DIR/reference"
fi

# Create consolidation README
cat > "$LEGACY_DIR/README.md" << 'EOF'
# Legacy LastPass Tooling Archive

This directory contains archived content from the old LastPass tooling directories:

- `backups/` - Old backup exports and scripts from `lastpass-secrets-backup/`
- `reference/` - Reference scripts from `lastpass-reference-scripts/`

## Migration Complete

All functionality has been consolidated into the unified `lastpass-vault` tool.

**Use this instead:**
```bash
cd /Users/bado/iccha/brighthive/lastpass-vault
./cli/secrets consolidate
./cli/secrets organize --materialize
```

## Old Directories

The following directories can be safely deleted after verifying migration:

- `/Users/bado/iccha/brighthive/lastpass-secrets-backup/`
- `/Users/bado/iccha/brighthive/lastpass-reference-scripts/`

**To delete (after verification):**
```bash
rm -rf /Users/bado/iccha/brighthive/lastpass-secrets-backup
rm -rf /Users/bado/iccha/brighthive/lastpass-reference-scripts
```
EOF

echo ""
echo "✅ Consolidation complete!"
echo ""
echo "📁 Legacy content archived to: $LEGACY_DIR"
echo ""
echo "🔄 Next steps:"
echo "   1. Verify the consolidation worked:"
echo "      cd $VAULT_DIR"
echo "      ./cli/secrets consolidate --skip-lastpass"
echo ""
echo "   2. After verification, you can delete old directories:"
echo "      rm -rf $BACKUP_DIR"
echo "      rm -rf $REFERENCE_DIR"
echo ""
echo "   3. Use the unified tool going forward:"
echo "      cd $VAULT_DIR"
echo "      ./cli/secrets --help"
echo ""
