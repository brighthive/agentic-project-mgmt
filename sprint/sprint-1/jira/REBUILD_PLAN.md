# Jira CLI Rebuild Plan

## Current State
- `jira_lib/` exists with solid foundation (config, models, client, operations)
- 31 passing tests, but only 8% total coverage
- Low coverage on critical modules:
  - `jira_client.py`: 27% (HTTP operations need mocking tests)
  - `jira_operations.py`: 22% (high-level ops need tests)
  - `jira_models.py`: 75% (from_api_response methods need tests)
- 35+ old scripts with hardcoded data (0% coverage)

## Goal
Build a proper CLI tool (`jira-cli`) that:
1. Is fully tested (TDD approach)
2. Has NO hardcoded data
3. Uses config files for all operations
4. Replaces all 35+ old scripts
5. Is composable and maintainable

## Architecture

```
jira/
├── jira_lib/              # Core library (existing, needs more tests)
│   ├── __init__.py
│   ├── jira_config.py     # ✅ 96% coverage
│   ├── jira_models.py     # ⚠️ 75% coverage (need model tests)
│   ├── jira_client.py     # ⚠️ 27% coverage (need HTTP mock tests)
│   ├── jira_operations.py # ⚠️ 22% coverage (need operation tests)
│   └── adf_builder.py     # ✅ 90% coverage
│
├── jira_cli/              # NEW - CLI tool
│   ├── __init__.py
│   ├── cli.py             # Main CLI entry point (Typer)
│   ├── config_loader.py   # Load YAML configs with validation
│   └── commands/
│       ├── __init__.py
│       ├── assign.py      # jira assign --config team.yaml
│       ├── sprint.py      # jira sprint add/list/create
│       ├── verify.py      # jira verify assignments/sprint
│       ├── create.py      # jira create epic/task
│       └── transition.py  # jira transition --status "In Progress"
│
├── tests/
│   ├── test_jira_config.py       # ✅ Existing
│   ├── test_adf_builder.py       # ✅ Existing
│   ├── test_jira_models.py       # NEW - model creation tests
│   ├── test_jira_client.py       # NEW - HTTP mock tests
│   ├── test_jira_operations.py   # NEW - operation tests
│   ├── test_config_loader.py     # NEW - CLI config tests
│   └── test_commands/
│       ├── test_assign.py         # NEW
│       ├── test_sprint.py         # NEW
│       ├── test_verify.py         # NEW
│       └── test_create.py         # NEW
│
├── config/                # Example configs (NO hardcoding)
│   ├── assignments.yaml   # Team assignments
│   ├── sprint-1.yaml      # Sprint 1 tickets
│   └── team.yaml          # Team member definitions
│
└── scripts/               # OLD scripts (deprecate after CLI works)
    └── (35+ scripts to be replaced)
```

## Phase 1: Complete Library Tests (TDD)

### 1.1 Test jira_models.py
- Test all `from_api_response` methods
- Test enum conversions
- Test edge cases (missing fields, null values)
- Target: 95%+ coverage

### 1.2 Test jira_client.py
- Mock all HTTP calls with `responses` or `pytest-mock`
- Test success paths (200, 201, 204)
- Test error paths (400, 401, 404, 500)
- Test timeout/connection errors
- Target: 90%+ coverage

### 1.3 Test jira_operations.py
- Mock client calls at the boundary
- Test all high-level operations
- Test error propagation
- Test edge cases
- Target: 90%+ coverage

## Phase 2: Build CLI Config Loader (TDD)

### 2.1 Create config schemas
```python
# TeamConfig
team_members:
  - name: Marwan
    emails:
      - marwan.samih@brighthive.io
      - marwan@brighthive.io
    tickets:
      - BH-150
      - BH-151

# SprintConfig
sprint:
  name: "Sprint 1"
  tickets:
    - BH-150
    - BH-151
```

### 2.2 Write tests first
- Test YAML parsing
- Test validation (Pydantic models)
- Test missing files
- Test invalid formats
- Test environment variable expansion

### 2.3 Implement config_loader.py
- Use Pydantic for validation
- Support env var substitution
- Clear error messages

## Phase 3: Build CLI Commands (TDD)

### 3.1 Command: jira assign
**Tests first:**
- Test loading assignment config
- Test assigning all team members
- Test error handling
- Test dry-run mode
- Test reporting

**Implementation:**
```bash
jira assign --config config/assignments.yaml
jira assign --config config/assignments.yaml --dry-run
jira assign --team-member Marwan --config config/assignments.yaml
```

### 3.2 Command: jira sprint
**Tests first:**
- Test listing sprints
- Test creating sprint
- Test adding tickets to sprint
- Test moving tickets between sprints

**Implementation:**
```bash
jira sprint list --project BH
jira sprint create --name "Sprint 2" --project BH
jira sprint add --sprint-id 123 --config config/sprint-1.yaml
jira sprint add --sprint-id 123 --tickets BH-150,BH-151
```

### 3.3 Command: jira verify
**Tests first:**
- Test verifying assignments
- Test verifying sprint contents
- Test mismatch detection
- Test reporting

**Implementation:**
```bash
jira verify assignments --config config/assignments.yaml
jira verify sprint --sprint-id 123 --config config/sprint-1.yaml
```

### 3.4 Command: jira create
**Tests first:**
- Test epic creation
- Test task creation with parent
- Test bulk creation

**Implementation:**
```bash
jira create epic --summary "Epic name" --project BH
jira create task --summary "Task name" --parent BH-100 --assignee marwan@brighthive.io
jira create bulk --config config/tasks.yaml
```

### 3.5 Command: jira transition
**Tests first:**
- Test single ticket transition
- Test bulk transition
- Test invalid status handling

**Implementation:**
```bash
jira transition BH-150 --status "In Progress"
jira transition --tickets-file ready.txt --status "In Progress"
jira transition --config config/assignments.yaml --status "In Progress"
```

## Phase 4: Integration & Migration

### 4.1 Add CLI to pyproject.toml
```toml
[project.scripts]
jira = "jira_cli.cli:app"
```

### 4.2 Create migration guide
- Document how to convert old scripts to CLI commands
- Create example configs for common operations
- Add deprecation warnings to old scripts

### 4.3 Validate with real operations
- Test against staging Jira
- Verify all Sprint 1 operations work
- Compare results with old scripts

## Phase 5: Cleanup

### 5.1 Archive old scripts
```bash
scripts/ → scripts/archive/
```

### 5.2 Update documentation
- README with CLI examples
- Command reference
- Configuration guide
- Migration guide

## Success Metrics

- [ ] Test coverage > 90% on all modules
- [ ] Zero hardcoded data in code
- [ ] All config in YAML files
- [ ] CLI replaces all 35+ scripts
- [ ] All Sprint 1 operations work via CLI
- [ ] Documentation complete
- [ ] Old scripts archived

## Dependencies to Add

```toml
dependencies = [
    "requests>=2.31.0",
    "pyyaml>=6.0.1",
    "typer>=0.9.0",        # CLI framework
    "pydantic>=2.5.0",     # Config validation
    "rich>=13.7.0",        # Beautiful CLI output
]

dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",  # For mocking
    "responses>=0.24.0",    # For HTTP mocking
    "pre-commit>=3.5.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "types-requests>=2.31.0",
    "types-pyyaml>=6.0.12",
]
```

## Timeline

- Phase 1: Complete library tests (2-3 hours)
- Phase 2: Config loader (1 hour)
- Phase 3: CLI commands (3-4 hours)
- Phase 4: Integration (1 hour)
- Phase 5: Cleanup (1 hour)

**Total: ~8-10 hours of focused work**

## Next Steps

1. Start with Phase 1.1: Complete jira_models.py tests
2. Then Phase 1.2: Complete jira_client.py tests (with mocking)
3. Then Phase 1.3: Complete jira_operations.py tests
4. Build CLI incrementally with TDD

This ensures:
- Solid foundation before building CLI
- Everything tested first
- No regression when refactoring
- Confidence in the implementation
