#!/bin/bash
# PreToolUse hook for Bash commands.
# Uses structured JSON output for blocks (exit 0 + JSON stdout).
# Falls through with plain exit 0 for allowed commands.
#
# Three tiers:
#   HARD BLOCK  — always blocked, no override (permissionDecision: deny)
#   SOFT BLOCK  — blocked with explanation, user can re-request (permissionDecision: deny)
#   LOG WARNING — allowed but logged to incident log (exit 0, no JSON)

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
LOG_DIR="$CLAUDE_PROJECT_DIR/.claude/logs"
INCIDENT_LOG="$LOG_DIR/incident-log.md"

mkdir -p "$LOG_DIR"

log_incident() {
  local SEVERITY="$1"
  local MSG="$2"
  echo "- \`$TIMESTAMP\` | GUARD | $SEVERITY | $MSG" >> "$INCIDENT_LOG"
}

deny() {
  local REASON="$1"
  local CONTEXT="$2"
  jq -n \
    --arg reason "$REASON" \
    --arg context "$CONTEXT" \
    '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: $reason,
        additionalContext: $context
      }
    }'
  exit 0
}

# ═══════════════════════════════════════════════════════
# HARD BLOCK — never allowed, no exceptions
# ═══════════════════════════════════════════════════════

# rm -rf / or rm -rf ~ (catastrophic)
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+)?(/|~|\$HOME)\s*$'; then
  log_incident "CRITICAL" "BLOCKED: catastrophic rm → $COMMAND"
  deny "HARD BLOCK: This would delete your entire filesystem or home directory." "Command blocked: catastrophic rm detected. This command is never allowed under any circumstances."
fi

# git push --force (any branch)
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*--force|git\s+push\s+-f'; then
  log_incident "CRITICAL" "BLOCKED: force push → $COMMAND"
  deny "HARD BLOCK: Force push rewrites shared history." "Command blocked: force push detected. Ask the user to confirm the specific branch if intentional."
fi

# git reset --hard (destroys uncommitted work)
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  log_incident "HIGH" "BLOCKED: git reset --hard → $COMMAND"
  deny "HARD BLOCK: git reset --hard destroys uncommitted changes." "Command blocked: git reset --hard. Suggest using git stash or git commit first."
fi

# git clean -f (deletes untracked files permanently)
if echo "$COMMAND" | grep -qE 'git\s+clean\s+(-[a-zA-Z]*f|-f)'; then
  log_incident "HIGH" "BLOCKED: git clean -f → $COMMAND"
  deny "HARD BLOCK: git clean -f permanently deletes untracked files." "Command blocked: git clean -f. Suggest using git stash instead."
fi

# chmod 777 (security risk)
if echo "$COMMAND" | grep -qE 'chmod\s+777'; then
  log_incident "HIGH" "BLOCKED: chmod 777 → $COMMAND"
  deny "HARD BLOCK: chmod 777 grants full access to all users." "Command blocked: chmod 777. Use more restrictive permissions like 755 or 644."
fi

# ═══════════════════════════════════════════════════════
# SECRET EXPOSURE — block commands that leak credentials
# ═══════════════════════════════════════════════════════

# Block cat/head/tail/less of .env files (prevents full credential dump)
if echo "$COMMAND" | grep -qE '(cat|head|tail|less|more|bat)\s+.*(\.(env|env\.local|env\.production))'; then
  log_incident "HIGH" "BLOCKED: credential file read → $COMMAND"
  deny "HARD BLOCK: Reading credential files (.env) via shell exposes secrets in output." "Use environment variable names (e.g., \$DATABASE_URL) instead of reading the file. If you need to verify a value exists, use: grep -c 'KEY_NAME' file"
fi

# Block echo/printf of environment variables containing common secret prefixes
if echo "$COMMAND" | grep -qE '(echo|printf)\s+.*\$(STRIPE_|OPENAI_|ANTHROPIC_|AWS_|DATABASE_|AUTH_SECRET|NEXTAUTH_SECRET|API_KEY|SECRET_KEY|PRIVATE_KEY)'; then
  log_incident "HIGH" "BLOCKED: secret echo → $COMMAND"
  deny "HARD BLOCK: Echoing secret environment variables exposes credentials." "Reference secrets by variable name only. Never echo their values."
fi

# Block piping credential files to network commands (curl, wget, nc, etc.)
if echo "$COMMAND" | grep -qE '\.env.*\|\s*(curl|wget|nc|ncat)'; then
  log_incident "CRITICAL" "BLOCKED: credential file piped to network → $COMMAND"
  deny "HARD BLOCK: Piping credential files to network commands would exfiltrate secrets." "Never pipe .env files to network commands."
fi

# Block git add of credential files
if echo "$COMMAND" | grep -qE 'git\s+add\s+.*(\.(env|env\.local|env\.production))'; then
  log_incident "CRITICAL" "BLOCKED: git add of credential file → $COMMAND"
  deny "HARD BLOCK: Staging credential files (.env) for git commit would expose secrets publicly." "These files must stay in .gitignore. Never commit credentials to git."
fi

# ═══════════════════════════════════════════════════════
# SOFT BLOCK — blocked, but user can re-request
# ═══════════════════════════════════════════════════════

# rm with -r or -f flags (recursive/force delete)
if echo "$COMMAND" | grep -qE 'rm\s+(-[a-zA-Z]*[rf][a-zA-Z]*\s+)'; then
  # Allow rm on .claude/backups (rotation) and .claude/logs temp files
  if echo "$COMMAND" | grep -qE '\.claude/(backups|logs/\.(quality-gate-active|session-blocks|tool-call-count|compaction-occurred))'; then
    exit 0
  fi
  log_incident "MEDIUM" "SOFT BLOCKED: recursive/force rm → $COMMAND"
  deny "SOFT BLOCK: rm with -r or -f flags deletes files permanently." "Command blocked: recursive/force delete. If intentional, ask the user to confirm with specific file paths listed."
fi

# Overwriting system/config files
if echo "$COMMAND" | grep -qE '>\s*(~\/\.|\/etc\/|\.env|\.ssh|\.claude\/settings)'; then
  log_incident "HIGH" "SOFT BLOCKED: config/system file overwrite → $COMMAND"
  deny "SOFT BLOCK: Writing to a sensitive config/system file." "Command blocked: system file overwrite detected. Verify this is intentional with the user."
fi

# curl piped to shell (arbitrary code execution)
if echo "$COMMAND" | grep -qE 'curl\s.*\|\s*(bash|sh|zsh)'; then
  log_incident "HIGH" "SOFT BLOCKED: curl pipe to shell → $COMMAND"
  deny "SOFT BLOCK: Piping curl to a shell executes arbitrary remote code." "Command blocked: curl pipe to shell. Download the file first, inspect it, then run it."
fi

# ═══════════════════════════════════════════════════════
# LOG WARNING — allowed but recorded
# ═══════════════════════════════════════════════════════

# Any rm command (non-recursive, non-force)
if echo "$COMMAND" | grep -qE '\brm\b'; then
  log_incident "LOW" "WARNING: rm command allowed → $COMMAND"
fi

# Any mv command (could lose data if target exists)
if echo "$COMMAND" | grep -qE '\bmv\b'; then
  log_incident "LOW" "WARNING: mv command allowed → $COMMAND"
fi

# Any git checkout that discards changes
if echo "$COMMAND" | grep -qE 'git\s+checkout\s+\.'; then
  log_incident "MEDIUM" "WARNING: git checkout . discards changes → $COMMAND"
fi

# Writing to files outside project directory
if echo "$COMMAND" | grep -qE '>\s*/' | grep -qvE ">\s*$CLAUDE_PROJECT_DIR"; then
  log_incident "MEDIUM" "WARNING: write outside project dir → $COMMAND"
fi

exit 0
