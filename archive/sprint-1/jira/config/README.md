# Configuration Files

This directory contains YAML configuration files for the Jira CLI tool.

## Structure

```
config/
├── examples/           # Example configurations
│   ├── assignments.yaml  # Team member ticket assignments
│   └── sprint.yaml      # Sprint ticket lists
└── README.md           # This file
```

## Configuration Types

### 1. Assignment Configuration (`assignments.yaml`)

Defines which tickets are assigned to which team members.

**Schema**:
```yaml
team:
  <member_name>:
    email: <valid_email>
    tickets:
      - <TICKET-ID>
      - <TICKET-ID>
```

**Validation Rules**:
- Email must be valid (validated by Pydantic EmailStr)
- Tickets list cannot be empty
- Team dict cannot be empty

**Example**:
```yaml
team:
  marwan:
    email: marwan@brighthive.io
    tickets:
      - BH-150
      - BH-151

  ahmed:
    email: ahmed@brighthive.io
    tickets:
      - BH-183
      - BH-184
```

**Usage**:
```bash
jira assign --config config/assignments.yaml
```

### 2. Sprint Configuration (`sprint.yaml`)

Defines which tickets belong to a sprint.

**Schema**:
```yaml
sprint_name: <sprint_name>
tickets:
  - <TICKET-ID>
  - <TICKET-ID>
```

**Validation Rules**:
- Sprint name is required
- Tickets list cannot be empty

**Example**:
```yaml
sprint_name: Sprint 1
tickets:
  - BH-150
  - BH-151
  - BH-152
```

**Usage**:
```bash
jira sprint add --config config/sprint.yaml
```

## Creating Your Own Configs

### From Examples
```bash
# Copy example and modify
cp config/examples/assignments.yaml config/my-assignments.yaml
# Edit with your data
vim config/my-assignments.yaml
# Use it
jira assign --config config/my-assignments.yaml
```

### From Scratch
Create a new YAML file following the schema above. The CLI will validate it before use.

## Validation

All configs are validated using Pydantic models:
- **Type safety**: Ensures correct data types
- **Email validation**: Real email format checking
- **Required fields**: Won't accept incomplete configs
- **Clear errors**: Get specific error messages if invalid

## Benefits of Config-Driven Approach

1. **No Hardcoding**: All data is external, easy to modify
2. **Version Control**: Track changes to assignments/sprints
3. **Reusability**: Same config file can be reused
4. **Validation**: Catch errors before API calls
5. **Documentation**: Config files serve as documentation

## Environment Variables

Jira credentials are loaded from `~/.config/jiratui/config.yaml`:
```yaml
jira_api_base_url: https://your-domain.atlassian.net
jira_api_username: your-email@domain.com
jira_api_token: your-api-token
```

This is separate from the action configs to keep credentials secure.
