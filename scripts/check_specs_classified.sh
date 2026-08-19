#!/usr/bin/env bash
# check_specs_classified.sh — prove the spec roadmap is clean enough to delegate.
#
# Every implementation spec in docs/specs/ must be classified: it carries a
# `status:` in the closed set below AND a `roadmap:` pointer to where its
# remainder lives. This is the machine form of the BH-1036 milestone — "all
# specs are done / closed / mixed" — so a hand-off engineer can confirm the
# roadmap is clean in one command instead of trusting a doc.
#
# Exit 0: every spec is classified; prints the per-bucket tally.
# Exit 1: at least one spec is missing a status, has an unknown status, or
#         is missing a roadmap: pointer. Prints exactly which, and why.
#
#   make check-specs-classified      # from repo root
#   ./scripts/check_specs_classified.sh
#
# A NEW file dropped into docs/specs/ is flagged until it is either classified
# (it is a spec) or added to NON_SPEC_FILES (it is a tracking/index/template
# doc). That refuse-to-pass-on-unmapped behavior is the point.

set -euo pipefail

SPECS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../docs/specs" && pwd)"

# Valid classifications. "done" = Shipped; "mixed" = Partial;
# "closed" = Superseded | Parked | Relocated. Keep in sync with THEMES.md.
readonly VALID_STATUSES="Shipped Partial Superseded Parked Relocated"

# Files in docs/specs/ that are NOT implementation specs and so are exempt
# from classification: the consolidation docs, the theme delegation units,
# the templates, and the BH-1255 trial tracking indexes. Add a new non-spec
# doc here (with a reason) rather than loosening the check.
readonly NON_SPEC_FILES=(
    "THEMES.md"                  # the 92-spec classification map itself
    "ROADMAP.md"                 # the dated frontier + delegation board
    "SPEC_TEMPLATE.md"           # full spec template
    "THEME_SPEC_TEMPLATE.md"     # lean theme template
    "HANDOVER_STATUS.md"         # BH-1255 trial handover map (tracking doc)
    "TICKET_LIST.md"             # BH-1255 trial ticket list (tracking doc)
)

is_non_spec() {
    local name="$1"
    # Theme delegation units are Draft-by-design, not classified specs.
    [[ "$name" == THEME-*.md ]] && return 0
    local exempt
    for exempt in "${NON_SPEC_FILES[@]}"; do
        [[ "$name" == "$exempt" ]] && return 0
    done
    return 1
}

# Read a single top-level frontmatter scalar (status / roadmap) from a file.
frontmatter_value() {
    local file="$1" key="$2"
    awk -v key="^${key}:" '
        $0 ~ key {
            sub(key, "")
            gsub(/["'\'']/, "")
            gsub(/^[[:space:]]+|[[:space:]]+$/, "")
            print
            exit
        }
    ' "$file"
}

declare -A bucket_count=()
problems=()
checked=0

for spec in "$SPECS_DIR"/*.md; do
    name="$(basename "$spec")"
    is_non_spec "$name" && continue
    checked=$((checked + 1))

    status="$(frontmatter_value "$spec" status)"
    roadmap="$(frontmatter_value "$spec" roadmap)"

    if [[ -z "$status" ]]; then
        problems+=("$name — no status: frontmatter")
        continue
    fi
    if [[ " $VALID_STATUSES " != *" $status "* ]]; then
        problems+=("$name — unknown status '$status' (want one of: $VALID_STATUSES)")
        continue
    fi
    if [[ -z "$roadmap" ]]; then
        problems+=("$name — status '$status' but no roadmap: pointer")
        continue
    fi

    bucket_count["$status"]=$(( ${bucket_count["$status"]:-0} + 1 ))
done

echo "Spec classification — $checked specs in docs/specs/"
echo "──────────────────────────────────────────────"
for status in $VALID_STATUSES; do
    printf "  %-11s %s\n" "$status" "${bucket_count[$status]:-0}"
done
echo "──────────────────────────────────────────────"

if (( ${#problems[@]} > 0 )); then
    echo
    echo "✗ ${#problems[@]} spec(s) not classified — roadmap is not clean:"
    for p in "${problems[@]}"; do
        echo "  - $p"
    done
    echo
    echo "Fix: give each a status: (${VALID_STATUSES// /, }) and a roadmap: pointer,"
    echo "or, if it is not a spec, add it to NON_SPEC_FILES in this script."
    exit 1
fi

echo "✓ all $checked specs classified (status + roadmap pointer) — clean to delegate"
