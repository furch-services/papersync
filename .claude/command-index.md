# Command Index

All system commands, their triggers, required tools, and invocation mode.

## Daily Rituals

| Command | Trigger | Tools | Mode | Description |
|---------|---------|-------|------|-------------|
| `/start` | Beginning of work day | Read, Write, Edit, Bash(date) | Self-execute | Load memory, create daily note, review tasks |
| `/sync` | Mid-day (after 3-4 hours) | Read, Write, Edit, Bash(date), Agent | Self-execute | Refresh memory, process scratchpad, review tasks |
| `/wrap-up` | End of work day | Read, Write, Edit, Bash(date), Agent | Self-execute | Daily audit, externalize knowledge, prep tomorrow |
| `/standup` | Start of day (quick mode) | Read, Edit, Glob, Bash(git,date) | Self-execute | Auto-generate yesterday/today/blockers from git + tasks |
| `/clear` | Context pressure or task completion | Read, Write, Edit, Bash(date) | Self-execute | Distill state, flush context, auto-resume |

## Quality & Review

| Command | Trigger | Tools | Mode | Description |
|---------|---------|-------|------|-------------|
| `/audit [scope]` | After completing a task/feature | Read, Agent, Write, Edit | Self-execute | Delegate quality review to auditor agent |
| `/review [target]` | Before merging code | Read, Agent, Glob, Grep, Bash(git) | Self-execute | Deep code review — security + performance + architecture |
| `/system-audit` | Monthly or after major changes | Read, Glob, Grep, Agent, Write, Edit, Bash(date,wc,find) | Self-execute | Deep infrastructure audit of entire system |
| `/drift-detect` | Monthly or when behaviour feels off | Read, Agent, Glob, Grep, Bash(wc,find,date) | Self-execute | Detect config drift — stale rules, contradictions, orphans |
| `/retro [period]` | End of sprint/week | Read, Write, Edit, Glob, Agent, Bash(date) | Self-execute | Sprint retrospective — analyze patterns, improve process |
| `/debt-map [dir]` | Before planning sprint work | Read, Agent, Glob, Grep, Bash(git,wc,find) | Self-execute | Map and prioritise technical debt across codebase |

## Problem Solving

| Command | Trigger | Tools | Mode | Description |
|---------|---------|-------|------|-------------|
| `/unstick [problem]` | When stuck on a problem 10+ min | Read, Agent, Grep, Glob, WebSearch | Self-execute | Root-cause analysis via unsticker agent |
| `/onboard [project]` | Starting work on unfamiliar codebase | Read, Agent, Glob, Grep, Bash(git,find,wc,ls) | Self-execute | Generate full codebase onboarding guide |

## Planning & Strategy

| Command | Trigger | Tools | Mode | Description |
|---------|---------|-------|------|-------------|
| `/brief [idea]` | Starting a new project | Read, Write, Edit, Agent, Glob, Bash(date) | Self-execute | Turn rough idea into structured project brief |
| `/launch [product]` | Preparing to launch a product/feature | Read, Write, Edit, Agent, Glob, Grep, WebSearch, WebFetch, Bash(date) | Self-execute | Full launch pipeline — competitive scan to GTM checklist |
| `/proposal [project]` | Client asks for a proposal | Read, Write, Edit, Agent, Glob, Bash(date) | Self-execute | Generate structured client proposal with scope and pricing |
| `/competitive-intel [market]` | Entering a new market or evaluating position | Read, Write, Edit, Agent, Glob, WebSearch, WebFetch, Bash(date) | Self-execute | Deep competitive analysis with strategic recommendations |

## Communication & Delivery

| Command | Trigger | Tools | Mode | Description |
|---------|---------|-------|------|-------------|
| `/report [topic]` | Need to present findings to stakeholders | Read, Write, Edit, Agent, Glob, Grep, Bash(date) | Self-execute | Generate audience-aware professional report |
| `/release [version]` | Shipping a new version | Read, Write, Edit, Glob, Grep, Bash(git,date) | Self-execute | Auto-generate release notes — technical + marketing + executive |
| `/handoff [recipient]` | Passing work to another person or AI | Read, Write, Edit, Glob, Grep, Bash(git,date) | Self-execute | Structured session handoff with full context briefing |

## System Building

| Command | Trigger | Tools | Mode | Description |
|---------|---------|-------|------|-------------|
| `/playbook [name]` | Repeating a manual workflow | Read, Write, Edit, Glob, Bash(date) | Self-execute | Record a workflow and auto-generate a reusable command |

## Auto-Trigger Conditions

Commands should be proactively invoked (not waiting for user) when:

| Condition | Command |
|-----------|---------|
| Session starts fresh | `/start` (if morning) or `/standup` (if quick) |
| 30+ tool calls in session | `/clear` |
| Compaction warning | `/clear` (emergency mode) |
| Discrete multi-step task completes | Consider `/clear` |
| Quality feels degraded | `/clear` |
| Stuck for 10+ minutes | `/unstick` |
| Feature/task completed | `/audit` |
| Before merging code | `/review` |
| Starting unfamiliar project | `/onboard` |
| Passing work to someone else | `/handoff` |
| System behaviour feels off | `/drift-detect` |

## Invocation Modes

- **Self-execute**: Read the command file and follow the procedure directly
- **Recommend**: Output `RECOMMEND: /command [args] — [reason]` for the orchestrator
