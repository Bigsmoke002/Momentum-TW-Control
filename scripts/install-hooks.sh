#!/usr/bin/env bash
# Installs git hooks that run scripts/check-private.sh before every commit and push.
set -e
cd "$(git rev-parse --show-toplevel)"
cat > .git/hooks/pre-commit <<'EOF'
#!/usr/bin/env bash
exec "$(git rev-parse --show-toplevel)/scripts/check-private.sh" --staged
EOF
cat > .git/hooks/pre-push <<'EOF'
#!/usr/bin/env bash
exec "$(git rev-parse --show-toplevel)/scripts/check-private.sh" --all
EOF
chmod +x .git/hooks/pre-commit .git/hooks/pre-push scripts/check-private.sh
echo "Hooks installed: pre-commit (staged changes) and pre-push (all tracked files)."
