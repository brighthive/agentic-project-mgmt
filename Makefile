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
# NOTE: env overlay scripts removed — env config is manual per-repo now
# APPLY_ENV := ./scripts/apply-env-overlay.sh
# OPEN_TERM := ./scripts/open-terminals.sh

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
# ONBOARDING — Layer 1 atomic primitives
# (Each target is idempotent. Re-running on a fully-set-up
#  workstation does nothing except verify state.)
# ══════════════════════════════════════════════════════════════

# Load user .env if present (provides AWS_*_PROFILE, LASTPASS_USER, etc.)
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Profile defaults (override in your .env)
AWS_MAIN_PROFILE        ?= brighthive-main
AWS_STAGING_PROFILE     ?= brighthive-staging
AWS_PRODUCTION_PROFILE  ?= brighthive-production
LASTPASS_USER           ?=
SIBLINGS_DIR            ?= ..
SECRETS_CACHE_TTL       ?= 86400
STATE_DIR               := .state
SECRETS_DIR             := secrets

# Source state helpers in every recipe via this prelude.
STATE_HELPERS = . scripts/state.sh

.PHONY: check-aws refresh-aws check-lastpass refresh-lastpass check-creds \
        check-siblings clone-siblings \
        pull-aws-secrets pull-lastpass pull-secrets \
        env-brightbot-local \
        status

# ── Credentials ───────────────────────────────────────────────

check-aws:  ## ① Verify AWS SSO sessions for main/staging/production
	@echo "── Checking AWS SSO sessions ──"
	@$(STATE_HELPERS); \
		for p in $(AWS_MAIN_PROFILE) $(AWS_STAGING_PROFILE) $(AWS_PRODUCTION_PROFILE); do \
			if aws sts get-caller-identity --profile "$$p" --query Account --output text >/dev/null 2>&1; then \
				acct=$$(aws sts get-caller-identity --profile "$$p" --query Account --output text); \
				echo "  ✓ $$p (account $$acct)"; \
				state_touch "aws/$$p"; \
			else \
				echo "  ✗ $$p (session expired or not configured — run: make refresh-aws)"; \
			fi; \
		done

refresh-aws:  ## ① Run `aws sso login` for any expired profile
	@echo "── Refreshing AWS SSO sessions ──"
	@$(STATE_HELPERS); \
		for p in $(AWS_MAIN_PROFILE) $(AWS_STAGING_PROFILE) $(AWS_PRODUCTION_PROFILE); do \
			if aws sts get-caller-identity --profile "$$p" >/dev/null 2>&1; then \
				echo "  ✓ $$p already valid (skipped)"; \
			else \
				echo "  → aws sso login --profile $$p"; \
				aws sso login --profile "$$p" || echo "  ✗ login failed for $$p"; \
				state_touch "aws/$$p"; \
			fi; \
		done

check-lastpass:  ## ① Verify LastPass session
	@echo "── Checking LastPass ──"
	@if lpass status >/dev/null 2>&1; then \
		echo "  ✓ logged in as $$(lpass status | awk '{print $$NF}')"; \
		$(STATE_HELPERS) && state_touch "lastpass/session"; \
	else \
		echo "  ✗ not logged in (run: make refresh-lastpass)"; \
	fi

refresh-lastpass:  ## ① Login to LastPass if session expired
	@if lpass status >/dev/null 2>&1; then \
		echo "  ✓ LastPass already logged in (skipped)"; \
	elif [ -z "$(LASTPASS_USER)" ]; then \
		echo "  ✗ LASTPASS_USER not set in .env"; exit 2; \
	else \
		echo "  → lpass login $(LASTPASS_USER)"; \
		lpass login "$(LASTPASS_USER)"; \
		$(STATE_HELPERS) && state_touch "lastpass/session"; \
	fi

check-creds: check-aws check-lastpass  ## ① Verify ALL credentials (AWS + LastPass)
	@echo ""
	@echo "  → run \`make refresh-aws\` and/or \`make refresh-lastpass\` to fix any ✗"

# ── Siblings ──────────────────────────────────────────────────

check-siblings:  ## ② List sibling repos: present / missing / optional
	@echo "── Sibling repos (configured in config/siblings.txt) ──"
	@grep -vE '^\s*(#|$$)' config/siblings.txt | while read -r entry; do \
		optional=0; \
		name="$$entry"; \
		case "$$entry" in *\?) optional=1; name="$${entry%\?}";; esac; \
		path="$(SIBLINGS_DIR)/$$name"; \
		if [ -d "$$path" ]; then \
			branch=$$(cd "$$path" && git branch --show-current 2>/dev/null || echo "?"); \
			dirty=""; cd "$$path" 2>/dev/null && git diff --quiet 2>/dev/null || dirty=" (dirty)"; \
			cd - >/dev/null 2>/dev/null; \
			printf "  ✓ %-40s branch=%s%s\n" "$$name" "$$branch" "$$dirty"; \
		elif [ "$$optional" = "1" ]; then \
			printf "  · %-40s optional, missing (skipped)\n" "$$name"; \
		else \
			printf "  ✗ %-40s MISSING — run: make clone-siblings\n" "$$name"; \
		fi; \
	done

clone-siblings:  ## ② git clone any missing sibling repos
	@echo "── Cloning missing siblings into $(SIBLINGS_DIR) ──"
	@grep -vE '^\s*(#|$$)' config/siblings.txt | while read -r entry; do \
		optional=0; \
		name="$$entry"; \
		case "$$entry" in *\?) optional=1; name="$${entry%\?}";; esac; \
		path="$(SIBLINGS_DIR)/$$name"; \
		if [ -d "$$path" ]; then \
			echo "  ✓ $$name (already cloned, skipped)"; \
		else \
			echo "  → git clone git@github.com:brighthive/$$name.git $$path"; \
			git clone "git@github.com:brighthive/$$name.git" "$$path" 2>&1 | tail -3 || { \
				[ "$$optional" = "1" ] && echo "    (optional, ignored)" || echo "    ✗ clone failed for $$name"; \
			}; \
		fi; \
	done

# ── Secret cache ──────────────────────────────────────────────

pull-aws-secrets:  ## ③ Pull AWS Secrets Manager values into secrets/aws/ (24h TTL)
	@echo "── Pulling AWS Secrets Manager values ──"
	@$(STATE_HELPERS); \
		mkdir -p $(SECRETS_DIR)/aws; \
		for env in main staging production; do \
			if state_skip_if_fresh "secrets/aws-$$env-pulled" "$(SECRETS_CACHE_TTL)" "secrets/aws/$$env.json"; then \
				continue; \
			fi; \
			account=$$(echo "$$env" | tr 'a-z' 'A-Z'); \
			[ "$$env" = "production" ] && account="PROD"; \
			[ "$$env" = "staging"    ] && account="STAGE"; \
			[ "$$env" = "main"       ] && account="MAIN"; \
			echo "  → aws-secrets-vault export --account $$account → $(SECRETS_DIR)/aws/$$env.json"; \
			./aws-secrets-vault/cli/secrets export --account "$$account" --output "$(SECRETS_DIR)/aws/$$env.json" 2>&1 | tail -3 || true; \
			state_touch "secrets/aws-$$env-pulled"; \
		done

pull-lastpass:  ## ③ Pull LastPass entries into secrets/lastpass.json (24h TTL)
	@echo "── Pulling LastPass secrets ──"
	@$(STATE_HELPERS); \
		mkdir -p $(SECRETS_DIR); \
		if state_skip_if_fresh "secrets/lastpass-pulled" "$(SECRETS_CACHE_TTL)" "secrets/lastpass.json"; then \
			exit 0; \
		fi; \
		echo "  → lastpass-vault export → $(SECRETS_DIR)/lastpass.json"; \
		./lastpass-vault/cli/secrets export --output "$(SECRETS_DIR)/lastpass.json" 2>&1 | tail -3 || true; \
		state_touch "secrets/lastpass-pulled"

pull-secrets: pull-aws-secrets pull-lastpass  ## ③ Pull all vault sources into ./secrets/

# ── Env materialization ───────────────────────────────────────

env-brightbot-local: pull-secrets  ## ④ Generate ../brightbot/.env from template + cached secrets
	@echo "── Materializing brightbot local .env ──"
	@python3 scripts/render_env.py \
		--template config/env-templates/brightbot-local.env.tmpl \
		--output $(SIBLINGS_DIR)/brightbot/.env \
		--secrets-dir $(SECRETS_DIR) \
		--state-dir $(STATE_DIR) \
		--key brightbot-local

# ── Status ────────────────────────────────────────────────────

status:  ## Show onboarding state at a glance
	@echo "── Onboarding state ──"
	@$(STATE_HELPERS); \
		for s in aws/$(AWS_MAIN_PROFILE) aws/$(AWS_STAGING_PROFILE) aws/$(AWS_PRODUCTION_PROFILE) lastpass/session secrets/aws-main-pulled secrets/aws-staging-pulled secrets/aws-production-pulled secrets/lastpass-pulled; do \
			age=$$(state_age_seconds "$$s"); \
			if [ "$$age" = "missing" ]; then \
				printf "  ✗ %-40s missing\n" "$$s"; \
			else \
				human=$$(state_format_age "$$age"); \
				printf "  ✓ %-40s $$human ago\n" "$$s"; \
			fi; \
		done

# ══════════════════════════════════════════════════════════════
# Help
# ══════════════════════════════════════════════════════════════

.PHONY: help

help:  ## Show this help
	@printf "\n  BrightHive Engineering-Leader Onboarding\n"
	@printf "  ─────────────────────────────────────────\n\n"
	@printf "  \033[1mLayer 1 — Onboarding primitives\033[0m  (idempotent, safe to re-run)\n"
	@grep -E '^[a-zA-Z_-]+:.*## ①|^[a-zA-Z_-]+:.*## ②|^[a-zA-Z_-]+:.*## ③|^[a-zA-Z_-]+:.*## ④' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "    \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@printf "\n  \033[1mLayer 2-4\033[0m  (coming soon: per-repo make local/staging/start, localstack, stagingstack, onboard)\n\n"
	@printf "  \033[1mLegacy — Slack integration\033[0m\n"
	@grep -E '^slack[a-zA-Z_-]*:.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "    \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@printf "\n  \033[1mUtilities\033[0m\n"
	@grep -E '^(status|help):.*## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "}; {printf "    \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@printf "\n  See ONBOARDING.md for the linear new-leader walkthrough.\n\n"

.DEFAULT_GOAL := help
