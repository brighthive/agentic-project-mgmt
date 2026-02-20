# Slack & Notion Integration Setup Guide

This guide explains how to set up Slack and Notion integrations for posting release notes and sprint updates.

---

## Slack Integration

### Option 1: Slack Webhook (Recommended for Release Notes)

#### Setup Steps

1. **Create Incoming Webhook**
   - Go to https://api.slack.com/apps
   - Select your workspace app (or create new)
   - Navigate to "Incoming Webhooks"
   - Click "Activate Incoming Webhooks"
   - Click "Add New Webhook to Workspace"
   - Select channel (e.g., `#releases`, `#engineering`)
   - Copy the webhook URL

2. **Set Environment Variable**
   ```bash
   export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
   ```

3. **Post Release Notes**
   ```bash
   cd /Users/bado/iccha/brighthive/project/sprint/sprint-1/scripts
   python post_to_slack.py --webhook-url $SLACK_WEBHOOK_URL
   ```

#### Webhook URL Storage

**Local Development:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

**GitHub Actions:**
```bash
# Add as repository secret
gh secret set SLACK_WEBHOOK_URL --body "https://hooks.slack.com/services/..."
```

**LastPass Vault:**
```bash
# Store in LastPass under "BrightHive Slack Webhook"
lpass add --notes "BrightHive Slack Webhook" <<< "$SLACK_WEBHOOK_URL"
```

---

### Option 2: Slack MCP Server (For Interactive Commands)

#### Prerequisites
```bash
npm install -g @modelcontextprotocol/server-slack
```

#### Configuration

Add to `~/.claude/mcp_config.json`:
```json
{
  "mcpServers": {
    "slack": {
      "command": "mcp-server-slack",
      "env": {
        "SLACK_BOT_TOKEN": "xoxb-your-bot-token",
        "SLACK_APP_TOKEN": "xapp-your-app-token"
      }
    }
  }
}
```

#### Get Slack Tokens

1. **Create Slack App**
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name: "BrightHive Bot"
   - Workspace: Your workspace

2. **Add Bot Token Scopes**
   - Navigate to "OAuth & Permissions"
   - Add scopes:
     - `chat:write` - Post messages
     - `channels:read` - List channels
     - `channels:history` - Read channel history
     - `users:read` - Get user info

3. **Install to Workspace**
   - Click "Install to Workspace"
   - Authorize the app
   - Copy "Bot User OAuth Token" (starts with `xoxb-`)

4. **Enable Socket Mode**
   - Navigate to "Socket Mode"
   - Enable Socket Mode
   - Generate app-level token with `connections:write` scope
   - Copy "App-Level Token" (starts with `xapp-`)

5. **Store Tokens Securely**
   ```bash
   # LastPass
   lpass add --notes "BrightHive Slack Bot Token" <<< "xoxb-..."
   lpass add --notes "BrightHive Slack App Token" <<< "xapp-..."

   # Or export to environment
   export SLACK_BOT_TOKEN="xoxb-..."
   export SLACK_APP_TOKEN="xapp-..."
   ```

#### Restart Claude Code
```bash
# Restart Claude Code to load MCP server
claude restart
```

---

### Option 3: Slack Web API (For Programmatic Access)

#### Install SDK
```bash
pip install slack-sdk
```

#### Example Script
```python
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])

try:
    response = client.chat_postMessage(
        channel="#releases",
        text="Sprint 1 Release Notes",
        blocks=[...],  # See post_to_slack.py for block format
    )
except SlackApiError as e:
    print(f"Error: {e}")
```

---

## Notion Integration

### Option 1: Notion MCP Server (Recommended)

#### Prerequisites
```bash
npm install -g @modelcontextprotocol/server-notion
```

#### Configuration

Add to `~/.claude/mcp_config.json`:
```json
{
  "mcpServers": {
    "notion": {
      "command": "mcp-server-notion",
      "env": {
        "NOTION_API_KEY": "secret_your_notion_api_key"
      }
    }
  }
}
```

#### Get Notion API Key

1. **Create Integration**
   - Go to https://www.notion.so/my-integrations
   - Click "New integration"
   - Name: "BrightHive Release Notes"
   - Select workspace
   - Copy "Internal Integration Token"

2. **Share Pages with Integration**
   - Open your Notion page (e.g., "Sprint 1 Release Notes")
   - Click "Share"
   - Invite "BrightHive Release Notes" integration
   - Grant edit access

3. **Store Token Securely**
   ```bash
   # LastPass
   lpass add --notes "BrightHive Notion API Key" <<< "secret_..."

   # Or export to environment
   export NOTION_API_KEY="secret_..."
   ```

4. **Restart Claude Code**
   ```bash
   claude restart
   ```

#### Usage in Claude Code

After setup, you can use Notion commands:
```
# Claude Code will have access to Notion tools
"Create a new page in Notion with Sprint 1 release notes"
"Update the roadmap page with completed milestones"
```

---

### Option 2: Notion API (For Automation)

#### Install SDK
```bash
pip install notion-client
```

#### Example Script
```python
from notion_client import Client

notion = Client(auth=os.environ["NOTION_API_KEY"])

# Create page
page = notion.pages.create(
    parent={"database_id": "your-database-id"},
    properties={
        "Name": {"title": [{"text": {"content": "Sprint 1 Release"}}]},
        "Status": {"select": {"name": "Published"}},
    },
    children=[
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [{"text": {"content": "Sprint 1 Release"}}]},
        },
        # ... more blocks
    ],
)
```

---

## Recommended Setup

### For Release Notes

1. **Slack:** Use Webhook (Option 1) - simplest for automated posting
2. **Notion:** Use MCP Server (Option 1) - integrates with Claude Code

### For Interactive Commands

1. **Slack:** Use MCP Server (Option 2) - enables Claude Code commands
2. **Notion:** Use MCP Server (Option 1) - enables Claude Code commands

---

## Automation Workflow

### GitHub Actions Release Workflow

Create `.github/workflows/release.yml`:

```yaml
name: Post Release Notes

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  post-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install requests

      - name: Post to Slack
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        run: |
          python project/sprint/sprint-1/scripts/post_to_slack.py
```

---

## Testing

### Test Slack Webhook
```bash
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message from BrightHive"}'
```

### Test Notion API
```bash
curl https://api.notion.com/v1/users \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2022-06-28"
```

---

## Security Best Practices

1. **Never commit tokens to git**
   - Use `.gitignore` for token files
   - Use environment variables
   - Use secrets management (LastPass, AWS Secrets Manager)

2. **Rotate tokens regularly**
   - Rotate every 90 days minimum
   - Rotate immediately if exposed

3. **Use minimal permissions**
   - Slack: Only grant necessary scopes
   - Notion: Only share required pages

4. **Monitor usage**
   - Check Slack app audit logs
   - Review Notion integration activity

---

## Troubleshooting

### Slack Webhook Not Working
- Verify webhook URL is correct
- Check channel exists
- Ensure workspace hasn't revoked webhook

### Slack MCP Not Loading
- Check `~/.claude/mcp_config.json` syntax
- Verify tokens are valid
- Restart Claude Code
- Check Claude Code logs: `~/.claude/logs/`

### Notion MCP Not Working
- Verify integration is shared with pages
- Check token is valid (not expired)
- Ensure workspace has access
- Restart Claude Code

---

## Resources

### Slack
- [Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Bot Token Scopes](https://api.slack.com/scopes)
- [Block Kit Builder](https://api.slack.com/block-kit)

### Notion
- [Getting Started](https://developers.notion.com/docs/getting-started)
- [API Reference](https://developers.notion.com/reference/intro)
- [Block Types](https://developers.notion.com/reference/block)

### MCP
- [Slack MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/slack)
- [Notion MCP Server](https://github.com/modelcontextprotocol/servers/tree/main/notion)

---

**Last Updated:** 2026-01-20
**Maintained By:** Platform Team
