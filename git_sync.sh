#!/bin/bash
while true; do
  # Check if there are any changes
  if [[ -n $(git status -s) ]]; then
    echo "🔄 Changes detected! Syncing to GitHub..."
    git add .
    git commit -m "Auto-sync: $(date +'%Y-%m-%d %H:%M:%S')"
    git push origin main
    echo "✅ Sync complete."
  else
    echo "😴 No changes found. Waiting..."
  fi
  sleep 60
done