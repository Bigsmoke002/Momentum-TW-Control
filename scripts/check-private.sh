#!/usr/bin/env bash
# Blocks commits/pushes that contain private data (see AGENTS.md).
#   scripts/check-private.sh            -> check staged changes (used by the pre-commit hook)
#   scripts/check-private.sh --all      -> check all tracked files (used by the pre-push hook)
#   scripts/install-hooks.sh            -> install both hooks
set -u
cd "$(git rev-parse --show-toplevel)" || exit 1

MODE="${1:---staged}"
if [ "$MODE" = "--all" ]; then
    FILES=$(git ls-files)
    content() { cat -- "$1" 2>/dev/null; }
else
    FILES=$(git diff --cached --name-only --diff-filter=ACMR)
    content() { git show ":$1" 2>/dev/null; }
fi

# name|regex
PATTERNS=(
    "Bluetooth/MAC address|([0-9A-Fa-f]{2}[:_-]){5}[0-9A-Fa-f]{2}"
    "Home directory path|/home/[a-z_][a-z0-9_-]*/"
    "Private IP address|(^|[^0-9.])(192\.168\.[0-9]{1,3}\.[0-9]{1,3}|10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3})"
    "E-mail address|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
    "Discord bot token|[MN][A-Za-z0-9_-]{23,25}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}"
    "GitHub/API token|(ghp_|gho_|github_pat_|sk-|xox[bp]-|AKIA)[A-Za-z0-9_-]{16,}"
    "Private key|-----BEGIN [A-Z ]*PRIVATE KEY-----"
    "Hard-coded secret|(password|passwd|secret|api[_-]?key|token)[\"']?[[:space:]]*[:=][[:space:]]*[\"'][^\"'[:space:]]{6,}[\"']"
)
# Allowed exceptions (e.g. GitHub noreply addresses, documentation placeholders)
ALLOW='noreply@anthropic\.com|users\.noreply\.github\.com|XX:XX:XX:XX:XX:XX'

found=0
for f in $FILES; do
    case "$f" in scripts/check-private.sh|*.png|*.jpg|*.jpeg|*.gif|*.ico) continue ;; esac
    text=$(content "$f") || continue
    for entry in "${PATTERNS[@]}"; do
        name="${entry%%|*}"; regex="${entry#*|}"
        hits=$(printf '%s\n' "$text" | grep -nEi -- "$regex" | grep -vEi -- "$ALLOW")
        if [ -n "$hits" ]; then
            found=1
            # print line numbers only, never the matched value itself
            echo "PRIVATE DATA? [$name] in $f, line(s): $(printf '%s\n' "$hits" | cut -d: -f1 | tr '\n' ' ')"
        fi
    done
done

if [ "$found" -ne 0 ]; then
    echo
    echo "Blocked: remove the private data above (see AGENTS.md) and try again."
    echo "If it is really a false positive, add it to ALLOW in scripts/check-private.sh."
    exit 1
fi
echo "check-private: OK ($MODE)"
