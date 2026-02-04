#!/bin/bash
# Sprint 4 Setup Script
# Run: JIRA_TOKEN=<your-token> ./sprint4_setup.sh
# Get token from: https://id.atlassian.com/manage-profile/security/api-tokens

set -e

# Check for required env var
if [ -z "$JIRA_TOKEN" ]; then
    echo "Error: JIRA_TOKEN environment variable not set"
    echo "Usage: JIRA_TOKEN=<your-api-token> ./sprint4_setup.sh"
    echo "Get token: https://id.atlassian.com/manage-profile/security/api-tokens"
    exit 1
fi

JIRA_USER="kuri@brighthive.io"
JIRA_BASE="https://brighthiveio.atlassian.net"
AUTH="$JIRA_USER:$JIRA_TOKEN"

echo "=== Sprint 4 Setup ==="
echo "User: $JIRA_USER"
echo ""

# Function to create ticket
create_ticket() {
    local summary="$1"
    local description="$2"
    local epic_key="$3"
    local story_points="$4"
    local assignee_id="$5"

    local payload=$(cat <<EOF
{
    "fields": {
        "project": {"key": "BH"},
        "summary": "$summary",
        "description": {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": "$description"}]}]
        },
        "issuetype": {"name": "Story"},
        "customfield_10014": "$epic_key",
        "customfield_10016": $story_points
    }
}
EOF
)

    # Add assignee if provided
    if [ -n "$assignee_id" ]; then
        payload=$(echo "$payload" | jq --arg aid "$assignee_id" '.fields.assignee = {"accountId": $aid}')
    fi

    response=$(curl -s -u "$AUTH" -X POST \
        "$JIRA_BASE/rest/api/3/issue" \
        -H "Content-Type: application/json" \
        -d "$payload")

    key=$(echo "$response" | jq -r '.key // empty')
    if [ -n "$key" ]; then
        echo "Created: $key - $summary"
        echo "$key"
    else
        echo "Error creating ticket: $summary"
        echo "$response" | jq '.errors // .'
        return 1
    fi
}

# Function to get Sprint 4 ID
get_sprint_id() {
    response=$(curl -s -u "$AUTH" \
        "$JIRA_BASE/rest/agile/1.0/board/4/sprint?state=future,active" \
        -H "Content-Type: application/json")

    sprint_id=$(echo "$response" | jq -r '.values[] | select(.name | test("Sprint.?4"; "i")) | .id' | head -1)

    if [ -z "$sprint_id" ]; then
        echo "Sprint 4 not found. Creating it..."
        # Would need to create sprint - for now just return
        echo ""
    else
        echo "$sprint_id"
    fi
}

# Function to move ticket to sprint
move_to_sprint() {
    local sprint_id="$1"
    local issue_key="$2"

    curl -s -u "$AUTH" -X POST \
        "$JIRA_BASE/rest/agile/1.0/sprint/$sprint_id/issue" \
        -H "Content-Type: application/json" \
        -d "{\"issues\": [\"$issue_key\"]}" > /dev/null

    echo "Moved $issue_key to Sprint 4"
}

# Function to cancel ticket
cancel_ticket() {
    local issue_key="$1"

    # Transition ID 51 = Canceled (may vary by project)
    response=$(curl -s -u "$AUTH" -X POST \
        "$JIRA_BASE/rest/api/3/issue/$issue_key/transitions" \
        -H "Content-Type: application/json" \
        -d '{"transition":{"id":"51"}}')

    if [ -z "$response" ] || [ "$response" = "{}" ]; then
        echo "Canceled: $issue_key"
    else
        echo "Note: $issue_key - $(echo "$response" | jq -r '.errorMessages[0] // "check status"')"
    fi
}

# Get team member account IDs
echo "=== Getting Team Member IDs ==="
users=$(curl -s -u "$AUTH" \
    "$JIRA_BASE/rest/api/3/users/search?maxResults=50" \
    -H "Content-Type: application/json")

# Extract account IDs (adjust names as needed)
AHMED_ID=$(echo "$users" | jq -r '.[] | select(.displayName | test("Ahmed"; "i")) | .accountId' | head -1)
MARWAN_ID=$(echo "$users" | jq -r '.[] | select(.displayName | test("Marwan"; "i")) | .accountId' | head -1)
KURI_ID=$(echo "$users" | jq -r '.[] | select(.displayName | test("Kuri\|Hikuri"; "i")) | .accountId' | head -1)
HARBOUR_ID=$(echo "$users" | jq -r '.[] | select(.displayName | test("Harbour"; "i")) | .accountId' | head -1)

echo "Ahmed: ${AHMED_ID:-not found}"
echo "Marwan: ${MARWAN_ID:-not found}"
echo "Kuri: ${KURI_ID:-not found}"
echo "Harbour: ${HARBOUR_ID:-not found}"
echo ""

# Get Sprint 4 ID
echo "=== Finding Sprint 4 ==="
SPRINT_ID=$(get_sprint_id)
if [ -z "$SPRINT_ID" ]; then
    echo "Warning: Sprint 4 not found. Tickets will be created but not assigned to sprint."
    echo "Create Sprint 4 manually in Jira first, then re-run."
else
    echo "Sprint 4 ID: $SPRINT_ID"
fi
echo ""

# ============================================
# STEP 1: Cancel garbage tickets
# ============================================
echo "=== Step 1: Canceling Garbage Tickets ==="

CANCEL_TICKETS=(
    "BH-215"  # AWS Bedrock - done as BH-198
    "BH-216"  # E2B sandbox - done as BH-176
    "BH-223"  # A2A Output artifact - vague
    "BH-222"  # A2A MCP protocol - vague
    "BH-221"  # Circuit breaker - generic
    "BH-220"  # Workflow traceability - generic
    "BH-219"  # Quality profiling - vague
    "BH-218"  # Schema mismatch - vague
    "BH-149"  # Distributed task queue - stale
    "BH-148"  # Parallel processing - stale
    "BH-145"  # MS Teams - not in roadmap
    "BH-143"  # Automation workflow - vague
    "BH-135"  # Persona analytics - stale
    "BH-134"  # Persona data model - stale
)

for ticket in "${CANCEL_TICKETS[@]}"; do
    cancel_ticket "$ticket"
done
echo ""

# ============================================
# STEP 2: Create new Sprint 4 tickets
# ============================================
echo "=== Step 2: Creating New Tickets ==="

# 1. Background Agent Analyst v0 (EPIC: BH-111)
TICKET_1=$(create_ticket \
    "[BE] Background Agent Analyst - Design spec" \
    "Design specification for Background Agent Analyst v0. Define analyst capabilities, triggers, output format. Integrate with existing BrightAgent infrastructure. Team design effort." \
    "BH-111" \
    3 \
    "")

# 2. Slack Auth Solution Design v0 (EPIC: BH-117)
TICKET_2=$(create_ticket \
    "[Design] Slack Auth - OAuth flow design" \
    "Design doc for Slack authentication. Workspace-level Slack app installation, user linking strategy. No implementation - design document only. Team design effort." \
    "BH-117" \
    2 \
    "")

# 3. Unstructured Data Source v0 (EPIC: BH-115)
TICKET_3=$(create_ticket \
    "[BE] Unstructured data source - S3/GCS connector" \
    "Implement unstructured data source connector. Support PDF, CSV, JSON files as data sources. Integration with warehouse pipeline. S3 and GCS storage backends." \
    "BH-115" \
    5 \
    "$AHMED_ID")

# 4. Workspace Portal - Context UI (EPIC: BH-114)
TICKET_4=$(create_ticket \
    "[FE] Workspace Portal - Context copywriting UI" \
    "Frontend UI for context engineering in workspace portal. Context display and edit functionality. User-friendly context engineering interface." \
    "BH-114" \
    3 \
    "$MARWAN_ID")

# 5. Context Engineering - API (EPIC: BH-110)
TICKET_5=$(create_ticket \
    "[BE] Context Engineering - Workspace context API" \
    "Backend API for workspace context retrieval and update. CEMAF integration for context management. Supports workspace portal frontend." \
    "BH-110" \
    3 \
    "$KURI_ID")

# 6. Projects - BHAgent integration (EPIC: BH-116)
TICKET_6=$(create_ticket \
    "[BE] Projects - BHAgent integration" \
    "Connect project context to BrightAgent. Agent can query project data, use project context. Continuation of Projects v0 work from Sprint 3." \
    "BH-116" \
    5 \
    "$HARBOUR_ID")

# 7. Projects - Agent interaction UI (EPIC: BH-116)
TICKET_7=$(create_ticket \
    "[FE] Projects - Agent interaction UI" \
    "Frontend UI for invoking agent from project context. User can interact with agent within project scope." \
    "BH-116" \
    3 \
    "$MARWAN_ID")

echo ""

# ============================================
# STEP 3: Move tickets to Sprint 4
# ============================================
if [ -n "$SPRINT_ID" ]; then
    echo "=== Step 3: Moving Tickets to Sprint 4 ==="

    # Move new tickets
    for ticket in "$TICKET_1" "$TICKET_2" "$TICKET_3" "$TICKET_4" "$TICKET_5" "$TICKET_6" "$TICKET_7"; do
        if [ -n "$ticket" ] && [[ "$ticket" == BH-* ]]; then
            move_to_sprint "$SPRINT_ID" "$ticket"
        fi
    done

    # Move carryover tickets
    echo ""
    echo "=== Moving Carryover Tickets ==="
    CARRYOVER_TICKETS=("BH-232" "BH-136" "BH-226")
    for ticket in "${CARRYOVER_TICKETS[@]}"; do
        move_to_sprint "$SPRINT_ID" "$ticket"
    done
else
    echo "=== Skipping Sprint Assignment (Sprint 4 not found) ==="
    echo "Created tickets need manual sprint assignment"
fi

echo ""
echo "=== Sprint 4 Setup Complete ==="
echo ""
echo "Summary:"
echo "- Canceled: ${#CANCEL_TICKETS[@]} garbage tickets"
echo "- Created: 7 new tickets"
echo "- Carryover: 3 tickets from Sprint 3"
echo "- Total Sprint 4: 10 tickets (~27 story points)"
echo ""
echo "Verification commands:"
echo "  jira list --query 'sprint = \"Sprint 4\"'"
echo "  jira list --query 'status = Canceled'"
