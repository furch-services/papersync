---
description: Analyze and produce a security checklist with structured process, quality checks, and system integration
---

# Security Checklist

## Purpose

Analyze and produce a comprehensive security checklist that delivers actionable, measurable results. This skill provides a structured process with quality validation, ensuring professional-grade output every time.

**Category**: Software Development

## Inputs

### Required
- **Objective**: What you want to achieve with this deliverable
- **Codebase Context**: Language, framework, and architecture

### Optional
- **Constraints**: Performance requirements, compatibility needs
- **Team Standards**: Existing coding conventions or style guides

## System Context

Before starting:
- Read `memory.md` for current project context and priorities
- Check `knowledge-base.md` for relevant learned rules or constraints
- Review any existing related documents in the project
- Note any active tasks in `Task Board.md` that relate to this deliverable

## Process

### Step 1: Context & Research
- Review any existing security checklist documents in the project
- Check knowledge-base.md for relevant learned rules or constraints
- Check memory.md for current project context and priorities
- Identify key stakeholders and their requirements
- Select the most appropriate framework: Clean Architecture, SOLID Principles, TDD/BDD

### Step 2: Analysis & Framework Application
- Apply the selected framework to structure the security checklist
- Identify gaps, opportunities, and risks
- Define success metrics: Deployment Frequency, Lead Time for Changes, Change Failure Rate, Mean Time to Recovery (MTTR)
- Document assumptions and dependencies
- Validate approach against industry best practices

### Step 3: Build the Deliverable
- Structure the security checklist using the output format below
- Include specific, actionable recommendations — not generic advice
- Add concrete numbers, timelines, and benchmarks where applicable
- Cross-reference with existing project documents for consistency
- Ensure every section adds value — remove filler

### Step 4: Quality Validation
- [ ] All required inputs have been addressed
- [ ] Recommendations are specific and actionable (not vague)
- [ ] Numbers and benchmarks are realistic and sourced
- [ ] Output format matches the specification below
- [ ] No contradictions with knowledge-base rules
- [ ] Follows best practice: Code reviews within 24 hours

## Output Format

```markdown
# Security Checklist

## Executive Summary
[2-3 sentence overview of the deliverable and key recommendations]

## Context & Objectives
- **Objective**: [What this achieves]
- **Audience**: [Who this is for]
- **Timeline**: [When this applies]

## Analysis
[Structured analysis using the selected framework]

## Recommendations
1. [Specific, actionable recommendation with expected impact]
2. [Specific, actionable recommendation with expected impact]
3. [Specific, actionable recommendation with expected impact]

## Implementation
| Action | Owner | Timeline | Priority |
|--------|-------|----------|----------|
| [Action item] | [Who] | [When] | [High/Medium/Low] |

## Success Metrics
| Metric | Current | Target | Measurement Method |
|--------|---------|--------|-------------------|
| [KPI] | [Baseline] | [Goal] | [How to measure] |

## Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Risk] | [H/M/L] | [H/M/L] | [Action] |

## Next Steps
- [ ] [Immediate next action]
- [ ] [Follow-up action]
- [ ] [Review date]
```

## Applicable Frameworks
- Clean Architecture
- SOLID Principles
- TDD/BDD
- 12-Factor App
- GitFlow/Trunk-Based Development
- Microservices vs Monolith decision tree
- OWASP Top 10

## Key Metrics
- Deployment Frequency
- Lead Time for Changes
- Change Failure Rate
- Mean Time to Recovery (MTTR)
- Code Coverage
- Cyclomatic Complexity
- Technical Debt Ratio

## Best Practices
- Code reviews within 24 hours
- Every PR should be reviewable in under 30 minutes
- Write tests before fixing bugs
- Automate everything that runs more than twice
- Document decisions, not just code

## After Completion

- Update `memory.md` if this deliverable changes project context or priorities
- Add any reusable learnings to `knowledge-nominations.md`
- If follow-up actions were identified, add them to `Task Board.md`
- Recommend related skills if additional work is needed
