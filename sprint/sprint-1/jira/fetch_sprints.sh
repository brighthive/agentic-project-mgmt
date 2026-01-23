#!/bin/bash
# Set these before running:
# export JIRA_BASE_URL="https://brighthiveio.atlassian.net"
# export JIRA_USERNAME="your-email@brighthive.io"
# export JIRA_TOKEN="your-api-token"

BASE_URL="${JIRA_BASE_URL:-https://brighthiveio.atlassian.net}"
USERNAME="${JIRA_USERNAME:-}"
TOKEN="${JIRA_TOKEN:-}"

if [ -z "$USERNAME" ] || [ -z "$TOKEN" ]; then
    echo "❌ Error: JIRA_USERNAME and JIRA_TOKEN environment variables must be set"
    echo "   export JIRA_USERNAME='your-email@brighthive.io'"
    echo "   export JIRA_TOKEN='your-api-token'"
    exit 1
fi

# Get board ID
BOARD_ID=$(curl -s -u "$USERNAME:$TOKEN" "$BASE_URL/rest/agile/1.0/board" | jq -r '.values[0].id')

# Get sprints
SPRINTS=$(curl -s -u "$USERNAME:$TOKEN" "$BASE_URL/rest/agile/1.0/board/$BOARD_ID/sprint")

# Get Sprint 1 and Sprint 2 IDs
SPRINT_1_ID=$(echo "$SPRINTS" | jq -r '.values[] | select(.name | contains("Sprint 1")) | .id')
SPRINT_2_ID=$(echo "$SPRINTS" | jq -r '.values[] | select(.name | contains("Sprint 2")) | .id')

echo "📊 Sprint 1 ID: $SPRINT_1_ID"
echo "📊 Sprint 2 ID: $SPRINT_2_ID"

# Fetch Sprint 1
if [ -n "$SPRINT_1_ID" ]; then
    echo -e "\n📦 Fetching Sprint 1 details..."
    curl -s -u "$USERNAME:$TOKEN" "$BASE_URL/rest/agile/1.0/sprint/$SPRINT_1_ID" | jq '.' > sprint_1_info.json
    
    # Fetch Sprint 1 tickets
    curl -s -u "$USERNAME:$TOKEN" \
        -H "Content-Type: application/json" \
        -X POST \
        -d "{\"jql\":\"sprint = $SPRINT_1_ID ORDER BY key ASC\",\"fields\":[\"summary\",\"status\",\"assignee\",\"priority\",\"issuetype\",\"labels\",\"customfield_10016\",\"parent\"],\"maxResults\":1000}" \
        "$BASE_URL/rest/api/3/search/jql" | jq '.' > sprint_1_tickets.json
    
    echo "  ✓ Saved sprint_1_info.json"
    echo "  ✓ Saved sprint_1_tickets.json"
fi

# Fetch Sprint 2
if [ -n "$SPRINT_2_ID" ]; then
    echo -e "\n📦 Fetching Sprint 2 details..."
    curl -s -u "$USERNAME:$TOKEN" "$BASE_URL/rest/agile/1.0/sprint/$SPRINT_2_ID" | jq '.' > sprint_2_info.json
    
    # Fetch Sprint 2 tickets
    curl -s -u "$USERNAME:$TOKEN" \
        -H "Content-Type: application/json" \
        -X POST \
        -d "{\"jql\":\"sprint = $SPRINT_2_ID ORDER BY key ASC\",\"fields\":[\"summary\",\"status\",\"assignee\",\"priority\",\"issuetype\",\"labels\",\"customfield_10016\",\"parent\"],\"maxResults\":1000}" \
        "$BASE_URL/rest/api/3/search/jql" | jq '.' > sprint_2_tickets.json
    
    echo "  ✓ Saved sprint_2_info.json"
    echo "  ✓ Saved sprint_2_tickets.json"
fi

echo -e "\n✅ Sprint data fetched"
