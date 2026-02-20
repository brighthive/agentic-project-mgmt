# ──────────────────────────────────────────────────────────────
# Agentic Project Management — Multi-Repo Dev Orchestrator
# ──────────────────────────────────────────────────────────────
#
# Usage:
#   make slack-local       Configure + start all 3 repos (local, no Cognito)
#   make slack-staging     Configure + start all 3 repos (staging Cognito)
#   make slack-env-local   Just configure .env files (no start)
#   make slack-env-staging Just configure .env files (no start)
#   make slack-checkout    Checkout the right branch on each repo
#   make slack-start       Start all 3 services (uses current .env)
#   make slack-status      Show branch + env mode for each repo
#   make slack-stop        Kill backgrounded services
#
# ──────────────────────────────────────────────────────────────

SHELL := /bin/bash

# ── Repo paths ────────────────────────────────────────────────
REPOS_DIR      := $(shell cd "$(CURDIR)/.." && pwd)
PLATFORM_CORE  := $(REPOS_DIR)/brighthive-platform-core
SLACK_SERVER   := $(REPOS_DIR)/brightbot-slack-server
WEBAPP         := $(REPOS_DIR)/brighthive-webapp

# ── Branches ──────────────────────────────────────────────────
PLATFORM_CORE_BRANCH := feature/slack-integration
SLACK_SERVER_BRANCH  := drchinca/BH-252/slack-oauth
WEBAPP_BRANCH        := drchinca/slack-integration

# ── Scripts ───────────────────────────────────────────────────
APPLY_ENV := ./scripts/apply-env-overlay.sh
OPEN_TERM := ./scripts/open-terminals.sh

# ── Start commands per repo ───────────────────────────────────
CMD_PLATFORM_CORE := cd $(PLATFORM_CORE) && npm run deploy:local
CMD_SLACK_SERVER  := cd $(SLACK_SERVER) && npm run dev
CMD_WEBAPP        := cd $(WEBAPP) && npm start

PIDS_DIR := $(CURDIR)/.pids

# ══════════════════════════════════════════════════════════════
# Combo targets: env + start
# ══════════════════════════════════════════════════════════════

.PHONY: slack-local slack-staging

slack-local: slack-checkout slack-env-local slack-start  ## Full local mode

slack-staging: slack-checkout slack-env-staging slack-start  ## Full staging mode

# ══════════════════════════════════════════════════════════════
# Checkout
# ══════════════════════════════════════════════════════════════

.PHONY: slack-checkout

slack-checkout:  ## Checkout slack integration branches on all repos
	@echo "── Checking out branches ──"
	@cd $(PLATFORM_CORE) && git checkout $(PLATFORM_CORE_BRANCH) 2>&1 | tail -1
	@cd $(SLACK_SERVER)   && git checkout $(SLACK_SERVER_BRANCH)  2>&1 | tail -1
	@cd $(WEBAPP)         && git checkout $(WEBAPP_BRANCH)        2>&1 | tail -1
	@echo ""

# ══════════════════════════════════════════════════════════════
# Env configuration
# ══════════════════════════════════════════════════════════════

.PHONY: slack-env-local slack-env-staging

slack-env-local:  ## Configure all repos for local mode (no Cognito)
	@echo "── Applying LOCAL env overlays ──"
	@$(APPLY_ENV) $(PLATFORM_CORE) envs/platform-core/local.env
	@$(APPLY_ENV) $(SLACK_SERVER)   envs/slack-server/local.env
	@$(APPLY_ENV) $(WEBAPP)         envs/webapp/local.env
	@echo ""
	@echo "  LOCAL mode:"
	@echo "    platform-core  LOCAL_DEV_MODE=true, JWKS disabled"
	@echo "    slack-server   LOCAL_DEV_MODE=true, Cognito bypassed"
	@echo "    webapp         REACT_APP_LOCAL_DEV=true, auto-login"
	@echo ""

slack-env-staging:  ## Configure all repos for staging mode (real Cognito)
	@echo "── Applying STAGING env overlays ──"
	@$(APPLY_ENV) $(PLATFORM_CORE) envs/platform-core/staging.env
	@$(APPLY_ENV) $(SLACK_SERVER)   envs/slack-server/staging.env
	@$(APPLY_ENV) $(WEBAPP)         envs/webapp/staging.env
	@echo ""
	@echo "  STAGING mode:"
	@echo "    platform-core  JWKS → staging Cognito pool"
	@echo "    slack-server   LOCAL_DEV_MODE=false, real Cognito"
	@echo "    webapp         REACT_APP_LOCAL_DEV=false, real login"
	@echo ""

# ══════════════════════════════════════════════════════════════
# Start / Stop
# ══════════════════════════════════════════════════════════════

.PHONY: slack-start slack-stop

slack-start:  ## Start all 3 services in Terminal tabs
	@echo "── Starting services ──"
	@echo "  platform-core → http://localhost:4000/graphql"
	@echo "  slack-server  → https://localhost:3000"
	@echo "  webapp        → http://localhost:3001"
	@echo ""
	@$(OPEN_TERM) "slack" \
		"$(CMD_PLATFORM_CORE)" \
		"$(CMD_SLACK_SERVER)" \
		"$(CMD_WEBAPP)"

slack-stop:  ## Kill services started by slack-start
	@echo "── Stopping services ──"
	@-lsof -ti :4000 | xargs kill 2>/dev/null && echo "  Killed :4000 (platform-core)" || true
	@-lsof -ti :3000 | xargs kill 2>/dev/null && echo "  Killed :3000 (slack-server)"  || true
	@-lsof -ti :3001 | xargs kill 2>/dev/null && echo "  Killed :3001 (webapp)"         || true
	@echo ""

# ══════════════════════════════════════════════════════════════
# Status
# ══════════════════════════════════════════════════════════════

.PHONY: slack-status

slack-status:  ## Show branch and env mode for each repo
	@echo "── Slack Integration Status ──"
	@echo ""
	@printf "  %-18s %-40s %s\n" "REPO" "BRANCH" "MODE"
	@printf "  %-18s %-40s %s\n" "──────────────────" "────────────────────────────────────────" "──────"
	@printf "  %-18s %-40s %s\n" \
		"platform-core" \
		"$$(cd $(PLATFORM_CORE) && git branch --show-current)" \
		"$$(grep -s '^LOCAL_DEV_MODE=' $(PLATFORM_CORE)/.env | cut -d= -f2 || echo '?')"
	@printf "  %-18s %-40s %s\n" \
		"slack-server" \
		"$$(cd $(SLACK_SERVER) && git branch --show-current)" \
		"$$(grep -s '^LOCAL_DEV_MODE=' $(SLACK_SERVER)/.env | cut -d= -f2 || echo '?')"
	@printf "  %-18s %-40s %s\n" \
		"webapp" \
		"$$(cd $(WEBAPP) && git branch --show-current)" \
		"$$(grep -s '^REACT_APP_LOCAL_DEV=' $(WEBAPP)/.env | cut -d= -f2 || echo '?')"
	@echo ""
	@echo "  Ports: platform-core=4000  slack-server=3000  webapp=3001"
	@echo ""

# ══════════════════════════════════════════════════════════════
# Help
# ══════════════════════════════════════════════════════════════

.PHONY: help

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
