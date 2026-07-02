# ELIS Discord / PO Checkpoint Governance

**Status:** Canonical — v1.1
**Date:** 2026-07-02
**Owner:** Carlos Rocha, Product Owner
**Applies to:** PM, PO Advisor, Platform Monitor, and PE threads

## 1. Purpose

This document defines how Discord is used for PE checkpoint communication.

- **Main Discord channel** = portfolio-level control and escalation.
- **#elis-pe-reports** = PO-visible macro-event notification channel (append-only)
- **A2A** = agent-to-agent operational communication channel
- **Kanban** = authoritative task and evidence record
- **GitHub** = canonical artefact and evidence record.

## 2. #elis-pe-reports Channel Permissions

Effective 2026-07-02, the @ELIS Agents role has the following permissions on #elis-pe-reports:

| Permission | Setting |
|-----------|---------|
| Send Messages | ✅ Allowed |
| Read Message History | ❌ Denied |

**Operational interpretation:**

- #elis-pe-reports is **append-only telemetry** for PO visibility.
- It is **not** an agent memory source, evidence store, handoff channel, or authority source.
- A2A is the agent-to-agent operational communication channel.
- Kanban is the authoritative task/evidence record.
- PO direct instruction remains the channel for approvals, exceptions, and escalations.

## 3. Thread Rules

1. Use one Discord thread per PE when thread-based coordination is available.
2. Keep PE checkpoint messages compact and versioned by reference to GitHub artefacts.
3. Use the main channel only for portfolio-level updates, blocking issues, escalation, or approval requests.
4. Use the PE thread for implementation checkpoints, validator status, and brief status packets.
5. Do not treat Discord history as canonical; always anchor final state in GitHub or Kanban.

## 4. Message Boundary Rules

- Keep Discord messages under 2,000 characters when possible.
- If a checkpoint exceeds the limit, split it into continuation messages.
- The first message should carry the primary status summary; continuation messages should be clearly labelled.
- Do not bury required evidence in a long unstructured thread post.

## 5. Compact PO Checkpoint Packet

A PE checkpoint message should normally include:

- PE ID
- current state
- commit hash or branch
- required artefact status
- blocker or next action
- whether the next owner is PM, implementer, validator, or PO

## 6. Boundary Summary

- **PM** coordinates and reports via Kanban and A2A.
- **Advisor** advises, diagnoses, and validates via A2A and Kanban.
- **Validators** report verdicts via A2A and Kanban.
- **Implementers** report build status and handoff evidence via A2A and Kanban.
- **#elis-pe-reports** is PO-visible macro-event notification only. Agents send to it but cannot read history.
- **No Discord message is authoritative unless the matching Kanban or GitHub artefact exists.**
