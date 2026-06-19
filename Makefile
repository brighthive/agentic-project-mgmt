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
# LAYER 0 — Prerequisite installation
# Each target checks first; installs only if missing.
# All targets are idempotent — safe to re-run.
# Requires: Homebrew on macOS, apt-get on Linux.
# ══════════════════════════════════════════════════════════════

.PHONY: install-brew install-awscli install-lastpasscli install-gh \
        install-python3 install-git install-prereqs check-prereqs \
        configure-aws-sso

# ── Homebrew (macOS only) ─────────────────────────────────────

install-brew:  ## ⓪ Install Homebrew if missing (macOS only)
	@if command -v brew >/dev/null 2>&1; then \
		echo "  ✓ brew $(shell brew --version 2>/dev/null | head -1 | awk '{print $$2}') (skipped)"; \
	elif [[ "$(shell uname)" == "Darwin" ]]; then \
		echo "  → Installing Homebrew..."; \
		/bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; \
	else \
		echo "  · Homebrew is macOS-only; skipping on $(shell uname)"; \
	fi

# ── AWS CLI ───────────────────────────────────────────────────

install-awscli:  ## ⓪ Install the AWS CLI if missing
	@if command -v aws >/dev/null 2>&1; then \
		echo "  ✓ aws $(shell aws --version 2>&1 | awk '{print $$1}' | cut -d/ -f2) (skipped)"; \
	else \
		brew_bin=$$(command -v brew 2>/dev/null || echo /opt/homebrew/bin/brew); \
		if [[ "$$(uname)" == "Darwin" ]] && "$$brew_bin" --version >/dev/null 2>&1; then \
			echo "  → brew install awscli"; \
			"$$brew_bin" install awscli; \
		elif [[ "$$(uname)" == "Linux" ]]; then \
			arch=$$(uname -m); [[ "$$arch" == "aarch64" ]] && arch="aarch64" || arch="x86_64"; \
			echo "  → Installing AWS CLI v2 for Linux/$$arch..."; \
			curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-$${arch}.zip" -o /tmp/awscliv2.zip; \
			unzip -q /tmp/awscliv2.zip -d /tmp/awscliv2; \
			sudo /tmp/awscliv2/aws/install; \
			rm -rf /tmp/awscliv2 /tmp/awscliv2.zip; \
		else \
			echo "  [ERROR] Cannot install AWS CLI automatically on this platform."; \
			echo "  Manual: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"; \
			exit 1; \
		fi; \
	fi

# ── LastPass CLI ──────────────────────────────────────────────

install-lastpasscli:  ## ⓪ Install the LastPass CLI (lpass) if missing
	@if command -v lpass >/dev/null 2>&1; then \
		echo "  ✓ lpass $(shell lpass --version 2>/dev/null | awk '{print $$NF}') (skipped)"; \
	else \
		brew_bin=$$(command -v brew 2>/dev/null || echo /opt/homebrew/bin/brew); \
		if "$$brew_bin" --version >/dev/null 2>&1; then \
			echo "  → brew install lastpass-cli"; \
			"$$brew_bin" install lastpass-cli; \
		elif command -v apt-get >/dev/null 2>&1; then \
			echo "  → apt-get install lastpass-cli"; \
			sudo apt-get install -y lastpass-cli; \
		else \
			echo "  [ERROR] Cannot install LastPass CLI automatically."; \
			echo "  Manual: https://github.com/lastpass/lastpass-cli#installation"; \
			exit 1; \
		fi; \
	fi

# ── GitHub CLI ────────────────────────────────────────────────

install-gh:  ## ⓪ Install the GitHub CLI (gh) if missing
	@if command -v gh >/dev/null 2>&1; then \
		echo "  ✓ gh $(shell gh --version 2>/dev/null | head -1 | awk '{print $$3}') (skipped)"; \
	else \
		brew_bin=$$(command -v brew 2>/dev/null || echo /opt/homebrew/bin/brew); \
		if "$$brew_bin" --version >/dev/null 2>&1; then \
			echo "  → brew install gh"; \
			"$$brew_bin" install gh; \
		elif command -v apt-get >/dev/null 2>&1; then \
			echo "  → Installing gh via apt..."; \
			curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
				| sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg; \
			echo "deb [arch=$$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
				| sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null; \
			sudo apt-get update -q && sudo apt-get install -y gh; \
		else \
			echo "  [ERROR] Cannot install gh automatically on this platform."; \
			echo "  Manual: https://github.com/cli/cli#installation"; \
			exit 1; \
		fi; \
	fi

# ── Python 3.11+ ──────────────────────────────────────────────

install-python3:  ## ⓪ Install Python 3.13 if no 3.11+ is found
	@if command -v python3.13 >/dev/null 2>&1 || \
	    command -v python3.12 >/dev/null 2>&1 || \
	    command -v python3.11 >/dev/null 2>&1; then \
		echo "  ✓ python3 $$($(PYTHON3) --version 2>&1 | awk '{print $$2}') (skipped)"; \
	else \
		brew_bin=$$(command -v brew 2>/dev/null || echo /opt/homebrew/bin/brew); \
		if "$$brew_bin" --version >/dev/null 2>&1; then \
			echo "  → brew install python@3.13"; \
			"$$brew_bin" install python@3.13; \
		elif command -v apt-get >/dev/null 2>&1; then \
			echo "  → apt-get install python3.13"; \
			sudo apt-get install -y python3.13; \
		else \
			echo "  [ERROR] Cannot install Python automatically on this platform."; \
			echo "  Manual: https://www.python.org/downloads/"; \
			exit 1; \
		fi; \
	fi

# ── git ───────────────────────────────────────────────────────

install-git:  ## ⓪ Install git if missing
	@if command -v git >/dev/null 2>&1; then \
		echo "  ✓ git $(shell git --version | awk '{print $$3}') (skipped)"; \
	else \
		brew_bin=$$(command -v brew 2>/dev/null || echo /opt/homebrew/bin/brew); \
		if "$$brew_bin" --version >/dev/null 2>&1; then \
			echo "  → brew install git"; \
			"$$brew_bin" install git; \
		elif command -v apt-get >/dev/null 2>&1; then \
			echo "  → apt-get install git"; \
			sudo apt-get install -y git; \
		else \
			echo "  [ERROR] Cannot install git automatically. Install from https://git-scm.com"; \
			exit 1; \
		fi; \
	fi

# ── AWS SSO profile setup ─────────────────────────────────────

configure-aws-sso:  ## ⓪ Print exact commands to configure AWS SSO profiles (run once per machine)
	@printf "\n  \033[1mAWS SSO profile setup\033[0m\n"
	@printf "  Run each command below and follow the interactive prompts.\n"
	@printf "  When asked for 'SSO session name' use the profile name shown.\n\n"
	@printf "  \033[36maws configure sso --profile brighthive-main\033[0m\n"
	@printf "    SSO session name: brighthive-main\n"
	@printf "    SSO start URL:    https://brighthive.awsapps.com/start\n"
	@printf "    SSO region:       us-east-1\n"
	@printf "    Default output:   json\n\n"
	@printf "  \033[36maws configure sso --profile brighthive-staging\033[0m\n"
	@printf "    SSO session name: brighthive-staging\n"
	@printf "    SSO start URL:    https://brighthive.awsapps.com/start\n"
	@printf "    SSO region:       us-east-1\n"
	@printf "    Default output:   json\n\n"
	@printf "  \033[36maws configure sso --profile brighthive-production\033[0m\n"
	@printf "    SSO session name: brighthive-production\n"
	@printf "    SSO start URL:    https://brighthive.awsapps.com/start\n"
	@printf "    SSO region:       us-east-1\n"
	@printf "    Default output:   json\n\n"
	@printf "  After setup, run: \033[36mmake refresh-aws\033[0m\n\n"

# ── install-prereqs: all of the above ─────────────────────────

install-prereqs: install-brew install-git install-awscli install-lastpasscli install-gh install-python3  ## ⓪ Install ALL prerequisites (idempotent — only installs what's missing)
	@echo ""
	@echo "  All prerequisites installed. Run \`make check-prereqs\` to verify."

# ── check-prereqs: verify without installing ──────────────────

check-prereqs:  ## ⓪ Check all prerequisites are installed (read-only, no installs)
	@echo "── Checking prerequisites ──"
	@ok=1; \
	for tool in brew git aws lpass gh; do \
		if command -v "$$tool" >/dev/null 2>&1; then \
			printf "  ✓ %-16s %s\n" "$$tool" "$$($$tool --version 2>&1 | head -1)"; \
		else \
			printf "  ✗ %-16s NOT FOUND — run: make install-$$tool\n" "$$tool" >&2; \
			ok=0; \
		fi; \
	done; \
	py="$(PYTHON3)"; \
	if [[ -n "$$py" ]]; then \
		printf "  ✓ %-16s %s\n" "python3" "$$("$$py" --version 2>&1)"; \
	else \
		printf "  ✗ %-16s NOT FOUND — run: make install-python3\n" "python3" >&2; \
		ok=0; \
	fi; \
	[[ "$$ok" == "1" ]] && echo "" && echo "  All prerequisites present." || \
		{ echo ""; echo "  Run \`make install-prereqs\` to install missing tools."; exit 1; }

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
# The *lead/ vault directory for the current user.  Derived from NAME.
# Override: NAME=matt  → LEAD_DIR=mattlead
LEAD_DIR                := $(NAME)lead

# Python interpreter — require 3.11+; reject the macOS Xcode stub.
PYTHON3 := $(shell command -v python3.13 || command -v python3.12 || command -v python3.11 || command -v python3)

# Source state helpers in every recipe via this prelude.
STATE_HELPERS = . scripts/state.sh

.PHONY: check-aws refresh-aws check-lastpass refresh-lastpass check-creds \
        check-siblings clone-siblings \
        pull-aws-secrets pull-lastpass pull-secrets \
        env-platform-core-local env-brightbot-local env-webapp-local env-webapp-staging \
        start-webapp stop-webapp start-core stop-core start-brightbot stop-brightbot \
        localstack stopstack stackstatus \
        status

# ── Credentials ───────────────────────────────────────────────

check-aws:  ## ① Verify AWS SSO sessions for main/staging/production
	@echo "── Checking AWS SSO sessions ──"
	@$(STATE_HELPERS); \
		for p in $(AWS_MAIN_PROFILE) $(AWS_STAGING_PROFILE) $(AWS_PRODUCTION_PROFILE); do \
			if acct=$$(aws sts get-caller-identity --profile "$$p" --query Account --output text 2>/dev/null); then \
				echo "  ✓ $$p (account $$acct)"; \
				state_touch "aws/$$p"; \
			else \
				echo "  ✗ $$p (session expired or not configured)"; \
				echo "    → run: make refresh-aws"; \
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

pull-aws-secrets: check-aws  ## ③ Pull AWS Secrets Manager values into secrets/aws/ (24h TTL)
	@echo "── Pulling AWS Secrets Manager values (NAME=$(NAME)) ──"
	@if [ -z "$(NAME)" ]; then \
		echo "  [ERROR] NAME is required. Example: NAME=matt make pull-aws-secrets"; \
		exit 2; \
	fi
	@if [ ! -d "$(LEAD_DIR)" ]; then \
		echo "  [ERROR] $(LEAD_DIR)/ not found."; \
		echo "  Ask your TechLead to run:  make onboard NAME=$(NAME)"; \
		echo "  Then you run:              NAME=$(NAME) make unpack"; \
		exit 1; \
	fi
	@$(STATE_HELPERS); \
		mkdir -p $(SECRETS_DIR)/aws; \
		if [ ! -f "$(LEAD_DIR)/secrets-manager/main_secrets.json" ] || \
		   [ ! -f "$(LEAD_DIR)/secrets-manager/stage_secrets.json" ] || \
		   [ ! -f "$(LEAD_DIR)/secrets-manager/prod_secrets.json" ] || \
		   [ "$${FORCE:-0}" = "1" ]; then \
			echo "  → $(PYTHON3) $(LEAD_DIR)/export_all.py secrets"; \
			$(PYTHON3) $(LEAD_DIR)/export_all.py secrets > /tmp/bh-agentic-aws-export.log 2>&1 || { \
				tail -20 /tmp/bh-agentic-aws-export.log; \
				exit 1; \
			}; \
		fi; \
		for env in main staging production; do \
			if state_skip_if_fresh "secrets/aws-$$env-pulled" "$(SECRETS_CACHE_TTL)" "secrets/aws/$$env.json"; then \
				continue; \
			fi; \
			case "$$env" in \
				main) source="$(LEAD_DIR)/secrets-manager/main_secrets.json" ;; \
				staging) source="$(LEAD_DIR)/secrets-manager/stage_secrets.json" ;; \
				production) source="$(LEAD_DIR)/secrets-manager/prod_secrets.json" ;; \
			esac; \
			if [ ! -f "$$source" ]; then \
				echo "  ✗ missing AWS export: $$source"; \
				exit 1; \
			fi; \
			echo "  → $$source → $(SECRETS_DIR)/aws/$$env.json"; \
			cp "$$source" "$(SECRETS_DIR)/aws/$$env.json"; \
			state_touch "secrets/aws-$$env-pulled"; \
		done

pull-lastpass:  ## ③ Pull LastPass entries into secrets/lastpass.json (24h TTL)
	@echo "── Pulling LastPass secrets (NAME=$(NAME)) ──"
	@if [ -z "$(NAME)" ]; then \
		echo "  [ERROR] NAME is required. Example: NAME=matt make pull-lastpass"; \
		exit 2; \
	fi
	@if [ ! -d "$(LEAD_DIR)" ]; then \
		echo "  [ERROR] $(LEAD_DIR)/ not found."; \
		echo "  Ask your TechLead to run:  make onboard NAME=$(NAME)"; \
		echo "  Then you run:              NAME=$(NAME) make unpack"; \
		exit 1; \
	fi
	@$(STATE_HELPERS); \
		mkdir -p $(SECRETS_DIR); \
		if state_skip_if_fresh "secrets/lastpass-pulled" "$(SECRETS_CACHE_TTL)" "secrets/lastpass.json"; then \
			exit 0; \
		fi; \
		if [ -f "$(LEAD_DIR)/lastpass-vault/lastpass_secrets.json" ] && [ "$${FORCE:-0}" != "1" ]; then \
			echo "  → $(LEAD_DIR)/lastpass-vault/lastpass_secrets.json → $(SECRETS_DIR)/lastpass.json"; \
			cp "$(LEAD_DIR)/lastpass-vault/lastpass_secrets.json" "$(SECRETS_DIR)/lastpass.json"; \
		else \
			echo "  → lastpass-vault sync"; \
			./lastpass-vault/cli/secrets sync > /tmp/bh-agentic-lastpass-sync.log 2>&1 || { \
				tail -20 /tmp/bh-agentic-lastpass-sync.log; \
				exit 1; \
			}; \
			echo "  → lastpass-vault export → $(SECRETS_DIR)/lastpass.json"; \
			./lastpass-vault/cli/secrets export --output "$(SECRETS_DIR)/lastpass.json" > /tmp/bh-agentic-lastpass-export.log 2>&1 || { \
				tail -20 /tmp/bh-agentic-lastpass-export.log; \
				exit 1; \
			}; \
		fi; \
		state_touch "secrets/lastpass-pulled"

pull-secrets: pull-aws-secrets pull-lastpass  ## ③ Pull all vault sources into ./secrets/

# ── Vault package — onboard a new engineering leader ─────────
#
# Usage:
#   make onboard NAME=matt          Package vault → mattlead-export.zip.enc
#   make unpack  NAME=matt          Unpack into mattlead/ (new leader runs this)
#   make verify-lead                Check that your *lead/ directory is complete
#
# NAME defaults to "kuri" (the current tech-lead's own vault).

.PHONY: onboard unpack verify-lead sync-vaults sync-langsmith

# NAME must be set by the caller: NAME=matt make pull-secrets
# Leaving NAME empty causes an explicit error instead of silently using the wrong vault.
NAME ?=

sync-langsmith:  ## ③ Snapshot LangSmith deployment shapes (auto-fetches admin key from AWS staging/platform/platform-core)
	@echo "── Syncing LangSmith deployment snapshots ──"
	@./scripts/snapshot_langsmith.sh

sync-vaults: check-creds  ## ③ Refresh ALL vault sources (lastpass + AWS + dynamo + langsmith) into $(NAME)lead/
	@echo "── Syncing all vaults into $(NAME)lead/ ──"
	@if [ -z "$(NAME)" ]; then echo "  [ERROR] NAME is required. Example: NAME=kuri make sync-vaults"; exit 2; fi
	@if [ ! -d "$(LEAD_DIR)" ]; then echo "  [ERROR] $(LEAD_DIR)/ not found — only the TechLead's own lead dir can be re-synced from live sources"; exit 1; fi
	@mkdir -p "$(LEAD_DIR)/lastpass-vault" "$(LEAD_DIR)/langsmith-vault"
	@echo "  ▸ LastPass: lastpass-vault sync + export"
	@./lastpass-vault/cli/secrets sync
	@./lastpass-vault/cli/secrets export --output "$(LEAD_DIR)/lastpass-vault/lastpass_secrets.json"
	@if [ -f "$(LEAD_DIR)/export_all.py" ]; then \
		echo "  ▸ AWS Secrets Manager + DynamoDB: $(LEAD_DIR)/export_all.py"; \
		$(PYTHON3) "$(LEAD_DIR)/export_all.py" all; \
	else \
		echo "  ⚠ $(LEAD_DIR)/export_all.py missing — skipping AWS / DynamoDB export (only the TechLead's lead dir has this)"; \
	fi
	@echo "  ▸ LangSmith deployment snapshots"
	@./scripts/snapshot_langsmith.sh
	@rm -rf "$(LEAD_DIR)/langsmith-vault" && cp -r langsmith-vault/data "$(LEAD_DIR)/langsmith-vault"
	@find "$(LEAD_DIR)/langsmith-vault" -name ".gitkeep" -delete 2>/dev/null || true
	@echo "  ▸ Verifying $(LEAD_DIR)/ completeness"
	@$(PYTHON3) scripts/package_kurilead.py verify --name "$(NAME)" || true
	@echo ""
	@echo "  ✓ All vaults synced. Run \`NAME=$(NAME) make onboard\` to package."

onboard:  ## ③ Package vault exports → {NAME}lead-export.zip.enc for new-leader handoff
	@echo "── Packaging vault for $(NAME) ──"
	@if [ -z "$(NAME)" ]; then echo "  [ERROR] NAME is required. Example: make onboard NAME=matt"; exit 2; fi
	@if [ -n "$(VAULT_PASSWORD)" ]; then \
		$(PYTHON3) scripts/package_kurilead.py package \
			--name "$(NAME)" \
			--output "$(NAME)lead-export.zip.enc" \
			--password "$(VAULT_PASSWORD)"; \
	else \
		$(PYTHON3) scripts/package_kurilead.py package \
			--name "$(NAME)" \
			--output "$(NAME)lead-export.zip.enc"; \
	fi

unpack:  ## ③ Decrypt + extract a vault package into {NAME}lead/ (new leaders run this)
	@echo "── Unpacking vault for $(NAME) ──"
	@if [ -z "$(NAME)" ]; then echo "  [ERROR] NAME is required. Example: NAME=matt make unpack"; exit 2; fi
	@if [ -n "$(VAULT_PASSWORD)" ]; then \
		$(PYTHON3) scripts/package_kurilead.py unpack \
			--name "$(NAME)" \
			--input "$(NAME)lead-export.zip.enc" \
			--password "$(VAULT_PASSWORD)"; \
	else \
		$(PYTHON3) scripts/package_kurilead.py unpack \
			--name "$(NAME)" \
			--input "$(NAME)lead-export.zip.enc"; \
	fi

verify-lead:  ## ③ Check that {NAME}lead/ has all expected vault export files
	@$(PYTHON3) scripts/package_kurilead.py verify --name "$(NAME)"

# ── Env materialization ───────────────────────────────────────

env-platform-core-local: pull-secrets  ## ④ Generate ../brighthive-platform-core/.env from template + cached secrets
	@echo "── Materializing platform-core local .env ──"
	@$(PYTHON3) scripts/render_env.py \
		--template config/env-templates/platform-core-local.env.tmpl \
		--output $(SIBLINGS_DIR)/brighthive-platform-core/.env \
		--secrets-dir $(SECRETS_DIR) \
		--state-dir $(STATE_DIR) \
		--key platform-core-local

env-brightbot-local: pull-secrets  ## ④ Generate ../brightbot/.env from template + cached secrets
	@echo "── Materializing brightbot local .env ──"
	@$(PYTHON3) scripts/render_env.py \
		--template config/env-templates/brightbot-local.env.tmpl \
		--output $(SIBLINGS_DIR)/brightbot/.env \
		--secrets-dir $(SECRETS_DIR) \
		--state-dir $(STATE_DIR) \
		--key brightbot-local

env-webapp-local: pull-aws-secrets  ## ④ Generate ../brighthive-webapp/.env.local for local dev
	@echo "── Materializing brighthive-webapp local .env.local ──"
	@$(PYTHON3) scripts/render_env.py \
		--template config/env-templates/webapp-local.env.tmpl \
		--output $(SIBLINGS_DIR)/brighthive-webapp/.env.local \
		--secrets-dir $(SECRETS_DIR) \
		--state-dir $(STATE_DIR) \
		--key webapp-local

env-webapp-staging: pull-aws-secrets  ## ④ Generate ../brighthive-webapp/.env.local for staging
	@echo "── Materializing brighthive-webapp staging .env.local ──"
	@$(PYTHON3) scripts/render_env.py \
		--template config/env-templates/webapp-staging.env.tmpl \
		--output $(SIBLINGS_DIR)/brighthive-webapp/.env.local \
		--secrets-dir $(SECRETS_DIR) \
		--state-dir $(STATE_DIR) \
		--key webapp-staging

# ── Status ────────────────────────────────────────────────────

# ── Per-service start/stop (orchestrator wrappers) ────────────

.PHONY: start-webapp stop-webapp start-core stop-core start-brightbot stop-brightbot \
        start-slack-server stop-slack-server \
        start-localstack stop-localstack localstack-infra \
        localstack stopstack stackstatus

_check_sibling = \
	@if [ ! -d "$(SIBLINGS_DIR)/$(1)" ]; then \
		echo "  [ERROR] $(1) not found. Run: make clone-siblings"; exit 1; \
	fi

start-webapp:  ## ④ Start brighthive-webapp against staging (background)
	$(call _check_sibling,brighthive-webapp)
	@NAME=$(NAME) $(MAKE) -C "$(SIBLINGS_DIR)/brighthive-webapp" staging-bg
	@echo "  → webapp  http://localhost:7420  (logs: /tmp/bh-webapp.log)"

stop-webapp:  ## ④ Stop the webapp
	@$(MAKE) -C "$(SIBLINGS_DIR)/brighthive-webapp" stop 2>/dev/null || true

start-core:  ## ④ Start brighthive-platform-core GraphQL API on :4040 (background)
	$(call _check_sibling,brighthive-platform-core)
	@NAME=$(NAME) $(MAKE) -C "$(SIBLINGS_DIR)/brighthive-platform-core" local

stop-core:  ## ④ Stop platform-core
	@$(MAKE) -C "$(SIBLINGS_DIR)/brighthive-platform-core" stop 2>/dev/null || true

start-brightbot:  ## ④ Start brightbot agent graph on :2024 (background)
	$(call _check_sibling,brightbot)
	@NAME=$(NAME) $(MAKE) -C "$(SIBLINGS_DIR)/brightbot" local

stop-brightbot:  ## ④ Stop brightbot
	@$(MAKE) -C "$(SIBLINGS_DIR)/brightbot" stop 2>/dev/null || true

start-slack-server:  ## ④ Start brightbot-slack-server on :3339 (background, local mode)
	$(call _check_sibling,brightbot-slack-server)
	@echo "  → starting slack-server (local mode)..."
	@cd "$(SIBLINGS_DIR)/brightbot-slack-server" && \
		unset SLACK_BOT_TOKEN SLACK_APP_TOKEN && \
		nohup yarn dev > /tmp/bh-slack-server.log 2>&1 & echo $$! > /tmp/bh-slack-server.pid
	@echo "  → slack-server http://localhost:3339  (logs: /tmp/bh-slack-server.log)"

stop-slack-server:  ## ④ Stop slack-server
	@if [ -f /tmp/bh-slack-server.pid ]; then \
		kill $$(cat /tmp/bh-slack-server.pid) 2>/dev/null && echo "  ✓ slack-server stopped" || true; \
		rm -f /tmp/bh-slack-server.pid; \
	else \
		lsof -ti tcp:3339 | xargs kill 2>/dev/null || true; \
	fi

# ── LocalStack (S3 + DynamoDB) ────────────────────────────────

LOCALSTACK_CONTAINER := brighthive-localstack
LOCALSTACK_PORT      := 4566
LOCAL_S3_BUCKET      := brighthive-local
LOCAL_NOTIF_TABLE    := brighthive-notifications-local
LOCAL_SUBS_TABLE     := brighthive-notification-subscriptions-local

start-localstack:  ## ④ Start LocalStack (S3 + DynamoDB) in Docker
	@if docker ps --format '{{.Names}}' | grep -q "^$(LOCALSTACK_CONTAINER)$$"; then \
		echo "  ✓ localstack already running"; \
	else \
		echo "  → starting localstack..."; \
		docker run -d \
			--name $(LOCALSTACK_CONTAINER) \
			-p $(LOCALSTACK_PORT):4566 \
			-e SERVICES=s3,dynamodb \
			-e DEFAULT_REGION=us-east-1 \
			-e AWS_DEFAULT_REGION=us-east-1 \
			localstack/localstack:3 > /dev/null; \
		echo "  → waiting for localstack to be ready..."; \
		for i in $$(seq 1 15); do \
			curl -sf http://localhost:$(LOCALSTACK_PORT)/_localstack/health >/dev/null 2>&1 && break; \
			sleep 1; \
		done; \
		echo "  ✓ localstack ready"; \
	fi

stop-localstack:  ## ④ Stop and remove LocalStack container
	@docker rm -f $(LOCALSTACK_CONTAINER) 2>/dev/null && echo "  ✓ localstack stopped" || true

localstack-infra: start-localstack  ## ④ Create S3 bucket + DynamoDB tables in LocalStack
	@echo "  → creating local infrastructure..."
	@AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
		aws --endpoint-url=http://localhost:$(LOCALSTACK_PORT) \
		s3 mb s3://$(LOCAL_S3_BUCKET) --region us-east-1 2>/dev/null || echo "  ✓ s3://$(LOCAL_S3_BUCKET) already exists"
	@AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
		aws --endpoint-url=http://localhost:$(LOCALSTACK_PORT) \
		dynamodb create-table \
		--table-name $(LOCAL_NOTIF_TABLE) \
		--attribute-definitions AttributeName=event_id,AttributeType=S \
		--key-schema AttributeName=event_id,KeyType=HASH \
		--billing-mode PAY_PER_REQUEST \
		--region us-east-1 2>/dev/null | grep -q TableName && echo "  ✓ $(LOCAL_NOTIF_TABLE) created" || echo "  ✓ $(LOCAL_NOTIF_TABLE) already exists"
	@AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test \
		aws --endpoint-url=http://localhost:$(LOCALSTACK_PORT) \
		dynamodb create-table \
		--table-name $(LOCAL_SUBS_TABLE) \
		--attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
		--key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
		--billing-mode PAY_PER_REQUEST \
		--region us-east-1 2>/dev/null | grep -q TableName && echo "  ✓ $(LOCAL_SUBS_TABLE) created" || echo "  ✓ $(LOCAL_SUBS_TABLE) already exists"
	@echo "  ✓ local infra ready"
	@echo ""
	@echo "    S3:      s3://$(LOCAL_S3_BUCKET)"
	@echo "    DynamoDB: $(LOCAL_NOTIF_TABLE)"
	@echo "    DynamoDB: $(LOCAL_SUBS_TABLE)"
	@echo "    Console: http://localhost:$(LOCALSTACK_PORT)"

localstack: localstack-infra start-brightbot start-slack-server  ## ④ Full local stack: LocalStack + brightbot + slack-server
	@echo ""
	@echo "  ┌──────────────────────────────────────────────────────────────┐"
	@echo "  │  BrightHive Local Stack                                      │"
	@echo "  ├──────────────────────────────────────────────────────────────┤"
	@echo "  │  localstack     http://localhost:4566   S3 + DynamoDB        │"
	@echo "  │  brightbot      http://localhost:2024   langgraph dev         │"
	@echo "  │  slack-server   http://localhost:3339   Socket Mode           │"
	@echo "  └──────────────────────────────────────────────────────────────┘"
	@echo ""
	@echo "  ngrok (OAuth):  make ngrok  →  separate terminal"
	@echo "  Stop all:       make stopstack"
	@echo "  Status:         make stackstatus"

stopstack: stop-slack-server stop-brightbot stop-core stop-localstack stop-webapp  ## ④ Stop all local services

stackstatus:  ## ④ Show running status of all local services
	@printf "  %-20s " "localstack";    curl -sf http://localhost:4566/_localstack/health >/dev/null 2>&1 && echo "running :4566" || echo "down"
	@printf "  %-20s " "brightbot";     lsof -ti tcp:2024 >/dev/null 2>&1 && echo "running :2024" || echo "down"
	@printf "  %-20s " "slack-server";  lsof -ti tcp:3339 >/dev/null 2>&1 && echo "running :3339" || echo "down"
	@printf "  %-20s " "platform-core"; lsof -ti tcp:4040 >/dev/null 2>&1 && echo "running :4040" || echo "down"
	@printf "  %-20s " "webapp";        lsof -ti tcp:7420 >/dev/null 2>&1 && echo "running :7420" || echo "down"

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
	@printf "  \033[1mLayer 0 — Install prerequisites\033[0m  (idempotent — skips already-installed tools)\n"
	@grep -hE '^[a-zA-Z_-]+:.*## ⓪' Makefile | \
		awk 'BEGIN {FS = ":.*## "}; {printf "    \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@printf "\n  \033[1mLayer 1 — Credentials, repos, secrets\033[0m  (idempotent, safe to re-run)\n"
	@grep -hE '^[a-zA-Z_-]+:.*## (①|②|③)' Makefile | \
		awk 'BEGIN {FS = ":.*## "}; {printf "    \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@printf "\n  \033[1mLayer 2 — Env files & service control\033[0m  (all require NAME=)\n"
	@grep -hE '^[a-zA-Z_-]+:.*## ④' Makefile | grep -vE '^(localstack|stopstack|stackstatus):' | \
		awk 'BEGIN {FS = ":.*## "}; {printf "    \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@printf "\n  \033[1mLayer 3 — Stack orchestration\033[0m  (coming soon: staging stack)\n"
	@grep -hE '^(localstack|stopstack|stackstatus):.*## ' Makefile | \
		awk 'BEGIN {FS = ":.*## "}; {printf "    \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@printf "\n  \033[1mLayer 5 — Longaeva trial tracker\033[0m  (refreshed manually + nightly cron)\n"
	@grep -hE '^longaeva-tracker[a-zA-Z_-]*:.*## ' Makefile | \
		awk 'BEGIN {FS = ":.*## "}; {printf "    \033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@printf "\n  \033[1mLegacy — Slack integration\033[0m\n"
	@grep -hE '^slack[a-zA-Z_-]*:.*## ' Makefile | \
		awk 'BEGIN {FS = ":.*## "}; {printf "    \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@printf "\n  \033[1mUtilities\033[0m\n"
	@grep -hE '^(status|help):.*## ' Makefile | \
		awk 'BEGIN {FS = ":.*## "}; {printf "    \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@printf "\n  See ONBOARDING.md for the linear new-leader walkthrough.\n\n"

# ── Longaeva trial tracker ───────────────────────────────────────────

.PHONY: longaeva-tracker longaeva-tracker-dry longaeva-tracker-no-slack longaeva-tracker-install-cron longaeva-tracker-uninstall-cron

# Resolve a Python that has PyYAML — checks the common venvs in the repo,
# falls back to system python3. Override with TRACKER_PYTHON=/path/to/python.
TRACKER_PYTHON ?= $(shell \
	for p in $(CURDIR)/aws-secrets-vault/.venv/bin/python \
	         $(CURDIR)/dynamo-vault/.venv/bin/python \
	         $(CURDIR)/.venv/bin/python; do \
		[ -x $$p ] && $$p -c 'import yaml' >/dev/null 2>&1 && { echo $$p; exit 0; }; \
	done; \
	command -v python3 >/dev/null && python3 -c 'import yaml' >/dev/null 2>&1 && { command -v python3; exit 0; }; \
	echo MISSING)

poc-tracker-deps:  ## ⑤ Verify PyYAML is reachable; print install hint if not
	@if [ "$(TRACKER_PYTHON)" = "MISSING" ]; then \
		echo "[tracker] No Python with PyYAML found. Install via: aws-secrets-vault/.venv/bin/pip install pyyaml"; \
		exit 3; \
	fi
	@echo "[tracker] using $(TRACKER_PYTHON)"

poc-tracker: poc-tracker-deps  ## ⑤ Refresh tracker for any client; CLIENT=<slug> (default: longaeva)
	@$(TRACKER_PYTHON) -m scripts.poc_tracker --client $(or $(CLIENT),longaeva)

poc-tracker-dry: poc-tracker-deps  ## ⑤ PoC tracker — dry run (no file write, no Slack)
	@$(TRACKER_PYTHON) -m scripts.poc_tracker --client $(or $(CLIENT),longaeva) --no-slack --dry-run

poc-tracker-no-slack: poc-tracker-deps  ## ⑤ PoC tracker without Slack post
	@$(TRACKER_PYTHON) -m scripts.poc_tracker --client $(or $(CLIENT),longaeva) --no-slack

# Shorthand for the common case — Longaeva is what we're running today.
longaeva-tracker: poc-tracker-deps  ## ⑤ Alias for `make poc-tracker CLIENT=longaeva`
	@$(TRACKER_PYTHON) -m scripts.poc_tracker --client longaeva

longaeva-tracker-dry: poc-tracker-deps  ## ⑤ Alias for `make poc-tracker-dry CLIENT=longaeva`
	@$(TRACKER_PYTHON) -m scripts.poc_tracker --client longaeva --no-slack --dry-run

longaeva-tracker-no-slack: poc-tracker-deps  ## ⑤ Alias for `make poc-tracker-no-slack CLIENT=longaeva`
	@$(TRACKER_PYTHON) -m scripts.poc_tracker --client longaeva --no-slack

longaeva-tracker-install-cron:  ## ⑤ Install nightly tracker refresh in crontab (06:00 ET / 10:00 UTC)
	@if crontab -l 2>/dev/null | grep -qF "longaeva-tracker"; then \
		echo "[tracker] cron entry already installed"; \
	else \
		entry='0 10 * * * cd $(CURDIR) && make longaeva-tracker >> /tmp/longaeva-tracker.log 2>&1'; \
		(crontab -l 2>/dev/null; echo "$$entry") | crontab -; \
		echo "[tracker] cron installed: $$entry"; \
	fi

longaeva-tracker-uninstall-cron:  ## ⑤ Remove the tracker cron entry
	@crontab -l 2>/dev/null | grep -vF "longaeva-tracker" | crontab - && \
		echo "[tracker] cron entry removed"

.DEFAULT_GOAL := help
