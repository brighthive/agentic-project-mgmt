#!/bin/bash
#
# Verify all changes from sprint closure session
# Run from: /Users/bado/iccha/brighthive
#

set -e

REPO_ROOT="/Users/bado/iccha/brighthive"
cd "$REPO_ROOT"

echo "==============================================================================="
echo "Verifying Sprint 1 Closure Changes"
echo "==============================================================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TOTAL=0
FOUND=0
MISSING=0

check_file() {
    local file="$1"
    local description="$2"
    TOTAL=$((TOTAL + 1))

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
        FOUND=$((FOUND + 1))
    else
        echo -e "${RED}✗${NC} $file ${YELLOW}(MISSING)${NC}"
        MISSING=$((MISSING + 1))
    fi
}

echo "Sprint 1 Documentation (12 files)"
echo "-----------------------------------"
check_file "project/sprint/sprint-1/SPRINT_1_RELEASE_NOTES.md"
check_file "project/sprint/sprint-1/SPRINT_1_MARKETING_RELEASE_NOTES.md"
check_file "project/sprint/sprint-1/INDEX.md"
check_file "project/sprint/sprint-1/SLACK_NOTION_INTEGRATION_SETUP.md"
check_file "project/sprint/sprint-1/CHANGES_SUMMARY.md"
check_file "project/sprint/sprint-1/ALL_CHANGES.txt"
check_file "project/sprint/sprint-1/changelogs/README.md"
check_file "project/sprint/sprint-1/changelogs/brighthive-platform-core.md"
check_file "project/sprint/sprint-1/changelogs/brighthive-webapp.md"
check_file "project/sprint/sprint-1/changelogs/brightbot.md"
check_file "project/sprint/sprint-1/changelogs/brighthive-data-organization-cdk.md"
check_file "project/sprint/sprint-1/changelogs/brighthive-data-workspace-cdk.md"
echo ""

echo "Automation Scripts (2 files)"
echo "-----------------------------"
check_file "project/sprint/scripts/generate_release_notes.py"
check_file "project/sprint/scripts/post_to_slack.py"
echo ""

echo "GitHub Actions Workflows (7 files)"
echo "-----------------------------------"
check_file ".github/workflows/sprint-release.yml"
check_file "brighthive-platform-core/.github/workflows/changelog.yml"
check_file "brighthive-webapp/.github/workflows/changelog.yml"
check_file "brightbot/.github/workflows/changelog.yml"
check_file "brighthive-data-organization-cdk/.github/workflows/changelog.yml"
check_file "brighthive-data-workspace-cdk/.github/workflows/changelog.yml"
check_file "brightbot-slack-server/.github/workflows/changelog.yml"
echo ""

echo "Configuration Files (6 files)"
echo "------------------------------"
check_file "brighthive-platform-core/cliff.toml"
check_file "brighthive-webapp/cliff.toml"
check_file "brightbot/cliff.toml"
check_file "brighthive-data-organization-cdk/cliff.toml"
check_file "brighthive-data-workspace-cdk/cliff.toml"
check_file "brightbot-slack-server/cliff.toml"
echo ""

echo "Documentation (2 files)"
echo "-----------------------"
check_file "project/sprint/AUTOMATION.md"
check_file "brightbot-slack-server/CHANGELOG.md"
echo ""

echo "==============================================================================="
echo "Verification Summary"
echo "==============================================================================="
echo -e "Total files checked: $TOTAL"
echo -e "${GREEN}Found: $FOUND${NC}"
echo -e "${RED}Missing: $MISSING${NC}"
echo ""

if [ $MISSING -eq 0 ]; then
    echo -e "${GREEN}✅ All changes verified successfully!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Some files are missing. Please review.${NC}"
    exit 1
fi
