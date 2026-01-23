# Notion Integration Setup

Configure Notion to work with sprint release notes automation.

## 1. Get Notion Integration Token

1. Go to: https://www.notion.so/my-integrations
2. Click **New integration**
3. Name: `BrightHive JIRA Integration`
4. Select your workspace
5. Click **Submit**
6. Copy the **Internal Integration Token**

Save as environment variable:
```bash
export NOTION_TOKEN="secret_xxxx..."
```

## 2. Create Sprint Database

1. In Notion, create a database called `Sprints`
2. Add these properties:
   - **Name** (Title) - Sprint name (e.g., "Sprint 1")
   - **Status** (Select) - Planning / Active / Completed
   - **Start Date** (Date)
   - **End Date** (Date)

3. For each sprint page, add sections with ## headings:
   ```markdown
   ## Sprint Goals
   - Goal 1
   - Goal 2

   ## Highlights
   - Key achievement 1
   - Key achievement 2

   ## Challenges & Learnings
   - Challenge 1
   - Challenge 2
   ```

4. Share database with integration:
   - Click `...` → **Add connections** → Select your integration

5. Copy Database ID from URL:
   ```
   https://notion.so/[workspace]/DATABASE_ID?v=...
                                 ^^^^^^^^^^^^
   ```

Save as environment variable:
```bash
export NOTION_SPRINT_DB_ID="abc123..."
```

## 3. Create Releases Database

1. Create a database called `Release Notes`
2. Add properties:
   - **Name** (Title) - Release name
   - **Date** (Date) - Release date
   - **Sprint** (Relation to Sprints)

3. Share database with integration:
   - Click `...` → **Add connections** → Select your integration

4. Copy Database ID:
```bash
export NOTION_RELEASES_DB_ID="xyz789..."
```

## 4. Set Environment Variables

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
# Notion Integration
export NOTION_TOKEN="secret_your_token_here"
export NOTION_SPRINT_DB_ID="your_sprint_database_id"
export NOTION_RELEASES_DB_ID="your_releases_database_id"
```

Then reload:
```bash
source ~/.zshrc
```

## 5. Test the Setup

```bash
cd /Users/bado/iccha/brighthive/jira
uv run python scripts/generate_sprint_release_notes.py
```

Enter sprint name and the script will:
1. ✅ Pull goals/highlights from Notion Sprint page
2. ✅ Fetch completed JIRA tickets
3. ✅ Generate rich release notes
4. ✅ Publish back to Notion Releases database

## Example Sprint Page Structure

```
Sprint 1

## Sprint Goals
- Implement data lake context engineering foundation
- Set up multi-org architecture
- Deploy initial security hardening

## Highlights
- Successfully migrated 3 organizations to new platform
- Zero downtime deployment achieved
- Team velocity increased by 25%

## Challenges & Learnings
- Initial RDS configuration needed adjustment
- CDK stack deployment took longer than expected
- Documentation gaps identified for new team members
```

The automation will pull this context and combine with JIRA tickets for complete release notes.

## Troubleshooting

**Error: "Failed to fetch Notion sprint"**
- Check `NOTION_TOKEN` is set correctly
- Verify integration has access to Sprint database
- Ensure sprint page exists with exact name match

**Error: "Failed to publish to Notion"**
- Check `NOTION_RELEASES_DB_ID` is correct
- Verify integration has access to Releases database
- Check database has correct properties (Name, Date)

**No goals/highlights pulled**
- Ensure sprint page uses `## Goals` and `## Highlights` headings
- Content should be in bulleted list format (`- item`)
- Check page structure matches example above
