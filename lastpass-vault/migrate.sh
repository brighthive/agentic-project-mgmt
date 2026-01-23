#!/bin/bash
# Migrate from old structure to new clean structure

set -e

OLD_BACKUP="/Users/bado/iccha/brighthive/lastpass-secrets-backup"
OLD_REFERENCE="/Users/bado/iccha/brighthive/lastpass-reference-scripts"
NEW_BASE="/Users/bado/iccha/brighthive/lastpass-vault"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║    MIGRATING TO CLEAN LASTPASS VAULT                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if old directories exist
if [ ! -d "$OLD_BACKUP" ]; then
    echo "❌ Old backup directory not found: $OLD_BACKUP"
    exit 1
fi

echo "📦 Migrating existing exports..."

# Copy CLI exports if they exist
if [ -d "$OLD_BACKUP/latest/individual" ]; then
    mkdir -p "$NEW_BASE/data/legacy/cli_exports"
    cp -r "$OLD_BACKUP/latest/"* "$NEW_BASE/data/legacy/cli_exports/" 2>/dev/null || true
    COUNT=$(ls -1 "$NEW_BASE/data/legacy/cli_exports/individual/"*.json 2>/dev/null | wc -l | xargs)
    echo "✅ Copied $COUNT CLI exports"
fi

# Copy manual entries if they exist
if [ -d "$OLD_BACKUP/manual_entries/individual" ]; then
    mkdir -p "$NEW_BASE/data/legacy/manual_entries"
    cp -r "$OLD_BACKUP/manual_entries/"* "$NEW_BASE/data/legacy/manual_entries/" 2>/dev/null || true
    COUNT=$(ls -1 "$NEW_BASE/data/legacy/manual_entries/individual/"*.json 2>/dev/null | wc -l | xargs)
    echo "✅ Copied $COUNT manual entries"
fi

# Archive reference scripts
if [ -d "$OLD_REFERENCE" ]; then
    mkdir -p "$NEW_BASE/data/legacy/reference"
    cp -r "$OLD_REFERENCE/"* "$NEW_BASE/data/legacy/reference/" 2>/dev/null || true
    echo "✅ Archived reference scripts"
fi

echo ""
echo "🔄 Now run the new CLI to import into catalog:"
echo ""
echo "   cd $NEW_BASE"
echo "   ./cli/secrets export"
echo "   ./cli/secrets analyze"
echo ""
echo "📊 Then check stats:"
echo "   ./cli/secrets stats"
echo ""
echo "🗑️  Old directories preserved at:"
echo "   $OLD_BACKUP"
echo "   $OLD_REFERENCE"
echo ""
echo "   You can delete them after verifying migration:"
echo "   rm -rf $OLD_BACKUP $OLD_REFERENCE"
echo ""
