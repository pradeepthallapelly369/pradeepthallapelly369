#!/usr/bin/env bash
# ==============================================================================
# Push all committed changes to GitHub main across all repositories
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Checking GitHub authentication..."
if ssh -T git@github.com -o ConnectTimeout=5 -o StrictHostKeyChecking=no 2>&1 | grep -q "successfully authenticated"; then
    echo "✅ SSH authentication verified with GitHub!"
    USE_SSH=true
else
    USE_SSH=false
fi

for d in */; do
    if [ -d "$d/.git" ]; then
        repo_name=$(basename "$d")
        unpushed=$(git -C "$d" log @{u}.. --oneline 2>/dev/null || true)
        
        if [ -n "$unpushed" ]; then
            echo ""
            echo "🚀 Pushing $repo_name to origin/main..."
            if [ "$USE_SSH" = true ]; then
                git -C "$d" remote set-url origin "git@github.com:pradeepthallapelly369/${repo_name}.git"
            fi
            git -C "$d" push origin main
            echo "✅ $repo_name successfully pushed!"
        fi
    fi
done

echo ""
echo "🎉 All repositories are up to date with origin/main!"
