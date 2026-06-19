#!/usr/bin/env bash
set -euo pipefail

# Snapshot every LangSmith / LangGraph Cloud deployment. Resolves the admin key from:
#   1. $LANGCHAIN_API_KEY env var (if set)
#   2. $LANGSMITH_API_KEY env var (if set)
#   3. AWS Secrets Manager: staging/platform/platform-core → LANGGRAPH_API_KEY (brighthive-staging SSO)
#
# Reads only — never mutates LangSmith state. Output: langsmith-vault/data/{env}/*.json

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

require() {
  command -v "${1}" >/dev/null 2>&1 || { echo "[ERROR] missing required command: ${1}" >&2; exit 127; }
}
require curl
require jq
require aws

resolve_key() {
  if [[ -n "${LANGCHAIN_API_KEY:-}" ]]; then echo "${LANGCHAIN_API_KEY}"; return; fi
  if [[ -n "${LANGSMITH_API_KEY:-}" ]]; then echo "${LANGSMITH_API_KEY}"; return; fi
  local secret_json
  secret_json="$(aws secretsmanager get-secret-value \
    --secret-id staging/platform/platform-core \
    --profile brighthive-staging \
    --query SecretString --output text 2>/dev/null || true)"
  if [[ -z "${secret_json}" ]]; then
    echo "[ERROR] no LangSmith admin key available." >&2
    echo "  Provide via env (LANGCHAIN_API_KEY=...) or refresh SSO: make refresh-aws" >&2
    echo "  Key location: AWS staging/platform/platform-core → LANGGRAPH_API_KEY" >&2
    exit 1
  fi
  echo "${secret_json}" | jq -r '.LANGGRAPH_API_KEY // empty'
}

main() {
  local key
  key="$(resolve_key)"
  if [[ -z "${key}" ]]; then
    echo "[ERROR] resolved an empty LangSmith API key" >&2
    exit 1
  fi
  LANGCHAIN_API_KEY="${key}" "${REPO_ROOT}/langsmith-vault/cli/snapshot" pull --all
}

main "$@"
