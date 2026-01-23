# Notion Management for Brighthive

**Last Updated**: 2026-01-14

This directory contains Notion workspace documentation and management tools.

---

## 🎯 Quick Start

### Current Setup (Working)

```bash
# Set your Notion token
export NOTION_TOKEN="ntn_Fl6076410608vPKtMDcJHs8tVWGYwErM1PpwPyNblJodCp"

# Search all accessible pages
notion-cli search "" -f json

# Get page content
notion-cli pages get <page-id> -f json
notion-cli blocks children <page-id> -f json
```

---

## 🛠️ CLI vs MCP: Which to Use?

### Notion CLI (✅ Recommended for Now)

**What it is**: NPM package that wraps Notion API
**Status**: ✅ Working perfectly

**Pros**:
- Simple, direct API access
- Works immediately with environment variable
- Great for scripting and automation
- Battle-tested, reliable

**Cons**:
- Requires manual token management
- Need to prefix every command with `NOTION_TOKEN=...`
- Not integrated into Claude Code's tool system

**Best for**:
- Bulk operations (cleanup, export)
- Scripts and automation
- One-off queries
- Current use until MCP is fully authenticated

---

### Notion MCP (✅ Ready to Use!)

**What it is**: Model Context Protocol server for Notion
**Status**: ✅ Connected and authenticated!

**Pros**:
- Native Claude Code integration
- OAuth authentication (more secure)
- Seamless tool access for Claude
- No environment variables needed per-command

**Cons**:
- Requires OAuth setup (not yet complete)
- Need to restart Claude Code after authentication
- More complex initial setup

**Best for**:
- Interactive Claude sessions
- Natural language queries about Notion
- Once OAuth is complete, replaces CLI for daily use

---

## 📝 Recommendation

### Interactive Work (Claude Code)
**Use MCP** ✅ - Native integration, OAuth authenticated, seamless experience

### Scripts/Automation
**Use CLI** 🔧 - More control, easier to script, better for bulk operations

### Both Have Their Place
- **MCP**: Daily queries, exploration, Claude integration
- **CLI**: Automation, bulk operations, scripting

---

## 📂 Files in This Directory

| File | Purpose |
|------|---------|
| `README.md` | This file - overview and tool comparison |
| `pages.md` | Workspace structure and key pages |
| `cleanup-analysis.md` | Workspace audit and cleanup recommendations |
| `DELETE_THESE_PAGES.txt` | List of 40 pages to delete |

---

## 🔧 Common Tasks

### Fetch a Notion page
```bash
# CLI approach (works now)
NOTION_TOKEN="ntn_Fl..." notion-cli pages get <page-id> -f json
notion-cli blocks children <page-id> -f json

# MCP approach (after OAuth)
# Just ask Claude: "Show me the Brighthive Platform Features page"
```

### Search for pages
```bash
# CLI
NOTION_TOKEN="ntn_Fl..." notion-cli search "platform features" -f json

# MCP (after OAuth)
# Ask Claude: "Find pages about platform features"
```

### Cleanup workspace
```bash
# CLI is better for bulk operations
# See cleanup-analysis.md and DELETE_THESE_PAGES.txt
```

---

## 🚀 Status Update (2026-01-14)

1. ✅ CLI working perfectly
2. ✅ Notion MCP configured and connected
3. ✅ OAuth authentication complete
4. ✅ Ready to use MCP for interactive work
5. ✅ CLI remains available for scripts/automation

**Next**: Test MCP by asking Claude natural language questions about Notion!

---

## 💡 Pro Tips

- **Export token to shell profile** to avoid typing it every time:
  ```bash
  echo 'export NOTION_TOKEN="ntn_Fl..."' >> ~/.zshrc
  source ~/.zshrc
  ```

- **Create aliases** for common commands:
  ```bash
  alias notion-search='notion-cli search'
  alias notion-get='notion-cli pages get'
  ```

- **Use jq** to parse JSON output:
  ```bash
  notion-cli search "" -f json | jq '.results[].properties.title'
  ```

---

**TL;DR**: Use CLI now. Switch to MCP after OAuth completes. Keep CLI for scripts.
