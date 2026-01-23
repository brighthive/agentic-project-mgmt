#!/bin/bash
# Soft test runner for lastpass-vault automation

set -e

echo "🧪 Running LastPass Vault Unit Tests"
echo "====================================="
echo ""

cd "$(dirname "$0")/.."

# Run each test file
python3 tests/unit/test_models.py
python3 tests/unit/test_analysis.py
python3 tests/unit/test_catalog.py
python3 tests/unit/test_config.py
python3 tests/unit/test_backup.py
python3 tests/unit/test_indexer.py
python3 tests/unit/test_app.py

echo ""
echo "✅ All tests passed!"
echo ""
