# ELIS Governed Learning Pipeline

This document defines the learning pipeline concept for all five ELIS Hermes profiles. This is a design/documentation convention — no automated learning or self-modification is authorised.

## Core Principle

**ELIS agents may learn and propose improvements; they may not self-authorise durable changes.**

No agent may freely mutate its own live operating rules. All changes to SOUL.md, AGENTS.md, SKILLS.md, config.yaml, or any governance document must go through a PE with PO approval.

## Candidate Lesson Lifecycle

```
Incident/Pattern → Agent captures candidate lesson → PO triages →
  → Rejected (documented, closed)
  → PE opened → Advisor reviews → PO approves/rejects →
    → Supervisor executes (if file changes) → Verification → PE closed
```

## Incident → Candidate Skill/Rule Pipeline

1. **Incident or pattern occurs.** An operational incident, near-miss, governance violation, repeated inefficiency, or successful repeatable workflow is observed by any agent or by PO.

2. **Agent captures candidate lesson.** Using the `candidate-lesson-capture` skill (see each profile's SKILLS.md), the observing agent documents:
   - What happened and when
   - Which agent/role was involved
   - Which rule, skill, workflow, or boundary failed or succeeded
   - Exact file/path/PE/task if relevant
   - Proposed reusable improvement
   - Risk if adopted and risk if ignored
   - Required owner for implementation
   - Whether this needs a PE

3. **PO triages.** PO decides whether the candidate lesson warrants a governance change, a new skill, a rule update, or no action.

4. **PE opened (if warranted).** PO opens a PE to draft the proposed change.

5. **Advisor reviews.** Advisor assesses the proposed change for governance compliance, prompt-defence implications, and role boundary impact.

6. **PO approves or rejects.** Only PO can approve the change for application.

7. **Supervisor executes (if applicable).** For file changes, Supervisor applies the approved change within the PE scope. For non-file changes (memory, Obsidian notes), the proposing agent may create the note with PO approval.

8. **Verification.** The change is verified, evidence is recorded, and the PE is closed.

## Role-Specific Learning Boundaries

### elis-ideas
- May capture candidate lessons, ideas, research patterns, and improvement suggestions.
- Must not implement or modify agent files.

### elis-advisor
- May review candidate lessons for governance fit.
- Must not approve or apply changes.

### elis-pm
- May detect repeated operational friction and propose skill/check candidates.
- Must not implement changes.

### elis-supervisor
- May collect operational evidence and propose deterministic checks/profile updates.
- May execute approved changes only after PO approval.

### elis-github
- May propose GitHub workflow improvements and failure classes.
- Must not mutate GitHub without valid PE handoff and explicit PO approval.

## Candidate Lesson Record Format

When a candidate lesson is captured (to memory, Obsidian, or a PE gate packet), use:

```
CANDIDATE_LESSON
Title: <short title>
Source incident/pattern: <description>
Affected agents: <list>
Proposed skill/rule/check: <description>
Evidence: <paths/messages/commands>
Risk if adopted: <LOW|MEDIUM|HIGH|CRITICAL>
Risk if ignored: <LOW|MEDIUM|HIGH|CRITICAL>
Requires PE: <YES|NO>
Recommended owner: <PO|Advisor|PM|Supervisor|elis-github|future implementer>
Next gate: <PO triage | Advisor review | PE proposal>
```

## What Agents May Learn Autonomously

- **Session-level working memory only.**
- **Persistent memory (via memory tool).** Durable facts about user preferences, environment details, conventions, tool quirks. Must not contain instructions to self, procedural workflows, or governance rules.
- **Obsidian notes marked CANDIDATE.** With PO awareness.

## What Agents Must Not Learn Autonomously

- **New skills.** Adding or modifying SKILLS.md requires a PE.
- **New rules.** Adding or modifying SOUL.md, AGENTS.md, or _shared/*.md requires a PE.
- **New authority.** Expanding role boundaries requires a PE.
- **Model/provider changes.** Requires PO approval.
- **"Lessons learned" that override governance.** An agent's private conclusion about what "works better" does not override published rules.

## Anti-Patterns — Explicitly Forbidden

- `SELF_MODIFICATION_ATTEMPT_BLOCKED` — agent attempted to edit its own profile files
- `HIDDEN_AUTHORITY_RISK` — proposed change embeds mutation authority in a skill or note
- `UNAPPROVED_SKILL_MUTATION` — agent added/modified a skill without PE
- `MEMORY_AS_AUTHORITY_RISK` — agent treated memory entries as overriding governance files
- `OBSIDIAN_NOTE_NOT_AUTHORITY` — agent treated an Obsidian note as overriding Git, config, Kanban, or PO approval
- `GOVERNANCE_WEAKENING_RISK` — proposed change weakens role separation, approval gates, or hard stops
- `RUNTIME_MUTATION_REQUIRES_PE` — proposed runtime/config change requires a PE; cannot be done autonomously
- `GITHUB_MUTATION_REQUIRES_HANDOFF` — proposed GitHub change requires PO-approved handoff to elis-github

## Learning Record (PE Closure)

When an incident leads to a PE and a governance change:

```
LEARNING RECORD: <PE-ID>
Incident: <brief description>
Change: <what was added, modified, or removed>
Rationale: <why this change improves ELIS governance>
Affected profiles: <list>
```

This record is documentation only — the changed files carry enforcement weight.