"""
ELIS A2A governed message semantics — shared policy module.

Gate 2E + Gate 3: validates sender role, recipient role, message type,
and timestamp governance (elis_sent_at) against the approved
Advisor ↔ Supervisor loopback policy table.

Inbound message types: request, ack, status.
policy_rejection is outbound-only — produced by TaskUpdater.reject().

Timestamp governance (Gate 3):
  - Inbound:  elis_sent_at (ISO 8601 UTC with literal Z)
  - Outbound: elis_processed_at (ISO 8601 UTC with literal Z)
  - Max stale age: 300 s
  - Max future skew: 30 s
  - Rejection codes: E_TS_MISSING, E_TS_MALFORMED, E_TS_STALE, E_TS_FUTURE
  - Deterministic failure — no success completion on timestamp failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

ALLOWED_SENDER_ROLES = frozenset({"advisor", "supervisor", "pm"})
ALLOWED_INBOUND_MESSAGE_TYPES = frozenset({"request", "ack", "status"})
PM_ALLOWED_RECIPIENTS = frozenset({"advisor", "supervisor", "github"})

# Timestamp governance constants (Gate 3)
MAX_STALE_AGE_S = 300
MAX_FUTURE_SKEW_S = 30


class RejectionCode:
    SELF_TARGET = "REJECTED_SELF_TARGET"
    MALFORMED_ENVELOPE = "REJECTED_MALFORMED_ENVELOPE"
    UNKNOWN_SENDER = "REJECTED_UNKNOWN_SENDER"
    UNSUPPORTED_TYPE = "REJECTED_UNSUPPORTED_TYPE"
    AUTONOMOUS_FOLLOW_ON = "REJECTED_AUTONOMOUS_FOLLOW_ON"
    DISALLOWED_RECIPIENT = "REJECTED_DISALLOWED_RECIPIENT"
    # Gate 3 — timestamp governance
    TS_MISSING = "E_TS_MISSING"
    TS_MALFORMED = "E_TS_MALFORMED"
    TS_STALE = "E_TS_STALE"
    TS_FUTURE = "E_TS_FUTURE"


@dataclass(frozen=True)
class PolicyResult:
    allowed: bool
    rejection_code: Optional[str] = None
    rejection_text: Optional[str] = None


# ── Timestamp helpers ────────────────────────────────────────────────


def _parse_iso8601_z(timestamp_str: str) -> Optional[datetime]:
    """Parse an ISO 8601 UTC timestamp string.

    Returns an aware UTC ``datetime``, or ``None`` on parse failure.
    Accepts the literal ``Z`` suffix and ``+00:00``.
    """
    try:
        normalised = timestamp_str.replace("Z", "+00:00")
        return datetime.fromisoformat(normalised)
    except (ValueError, TypeError):
        return None


def _utcnow_aware() -> datetime:
    """Return the current time as an aware UTC datetime."""
    return datetime.now(timezone.utc)


def validate_timestamp(
    *,
    elis_sent_at: Optional[str],
) -> PolicyResult:
    """Validate ``elis_sent_at`` against Gate 3 timestamp governance rules.

    Args:
        elis_sent_at: ISO 8601 UTC timestamp string (or ``None``).

    Returns:
        ``PolicyResult`` — allowed or rejected with one of
        ``E_TS_MISSING``, ``E_TS_MALFORMED``, ``E_TS_STALE``, ``E_TS_FUTURE``.
    """
    if elis_sent_at is None:
        return PolicyResult(
            allowed=False,
            rejection_code=RejectionCode.TS_MISSING,
            rejection_text=(
                "REJECTED: missing required timestamp field (elis_sent_at)."
            ),
        )

    sent_at = _parse_iso8601_z(elis_sent_at)
    if sent_at is None:
        return PolicyResult(
            allowed=False,
            rejection_code=RejectionCode.TS_MALFORMED,
            rejection_text=(
                f"REJECTED: malformed timestamp {elis_sent_at!r}. "
                "Expected ISO 8601 UTC (e.g. 2026-06-18T12:00:00Z)."
            ),
        )

    now = _utcnow_aware()

    # Stale check — message too old
    age_s = (now - sent_at).total_seconds()
    if age_s > MAX_STALE_AGE_S:
        return PolicyResult(
            allowed=False,
            rejection_code=RejectionCode.TS_STALE,
            rejection_text=(
                f"REJECTED: timestamp too old "
                f"({age_s:.0f}s > {MAX_STALE_AGE_S}s max stale age)."
            ),
        )

    # Future-skew check — clock drift / misconfigured sender
    if sent_at > now:
        skew_s = (sent_at - now).total_seconds()
        if skew_s > MAX_FUTURE_SKEW_S:
            return PolicyResult(
                allowed=False,
                rejection_code=RejectionCode.TS_FUTURE,
                rejection_text=(
                    f"REJECTED: timestamp too far in the future "
                    f"({skew_s:.0f}s > {MAX_FUTURE_SKEW_S}s max future skew)."
                ),
            )

    return PolicyResult(allowed=True)


# ── Message validation ───────────────────────────────────────────────


def validate_message(
    *,
    sender_role: Optional[str],
    message_type: Optional[str],
    recipient_role: str,
    declared_target_role: Optional[str] = None,
    elis_sent_at: Optional[str] = None,
) -> PolicyResult:
    """Validate an incoming message against the Gate 2E+Gate 3 policy table.

    Args:
        sender_role: Value of ``Message.metadata.elis_sender_role``.
        message_type: Value of ``Message.metadata.elis_message_type``.
        recipient_role: The role of the agent receiving the message
                        (``"advisor"`` or ``"supervisor"``).
        declared_target_role: Value of ``Message.metadata.elis_target_role``,
                              if present.  Used for PM destination allowlist
                              enforcement.
        elis_sent_at: Value of ``Message.metadata.elis_sent_at`` (Gate 3).
                       ISO 8601 UTC timestamp with literal ``Z``.

    Returns:
        ``PolicyResult`` with allowed=True/False and rejection details if denied.
    """
    # Malformed: missing core metadata
    if sender_role is None or message_type is None:
        return PolicyResult(
            allowed=False,
            rejection_code=RejectionCode.MALFORMED_ENVELOPE,
            rejection_text=(
                "REJECTED: missing required metadata fields "
                "(elis_sender_role, elis_message_type)."
            ),
        )

    # ── Gate 3: timestamp validation ──────────────────────────────────
    ts_result = validate_timestamp(elis_sent_at=elis_sent_at)
    if not ts_result.allowed:
        return ts_result
    # ── End Gate 3 ─────────────────────────────────────────────────────

    # Self-target (must fire before unknown sender — GitHub→GitHub returns
    # SELF_TARGET, not UNKNOWN_SENDER).
    if sender_role == recipient_role:
        return PolicyResult(
            allowed=False,
            rejection_code=RejectionCode.SELF_TARGET,
            rejection_text=(
                f"REJECTED: self-target not allowed "
                f"({sender_role} → {recipient_role})."
            ),
        )

    # Unknown sender
    if sender_role not in ALLOWED_SENDER_ROLES:
        return PolicyResult(
            allowed=False,
            rejection_code=RejectionCode.UNKNOWN_SENDER,
            rejection_text=(
                f"REJECTED: unknown sender role {sender_role!r}. "
                f"Allowed: {sorted(ALLOWED_SENDER_ROLES)}."
            ),
        )

    # PM destination allowlist — target must be in the approved recipient set.
    # Falls back to recipient_role when declared_target_role is not set, so
    # PM→Ideas and other disallowed routes are rejected even without an
    # explicit elis_target_role.
    if sender_role == "pm":
        effective_target = (
            declared_target_role
            if declared_target_role is not None
            else recipient_role
        )
        if effective_target not in PM_ALLOWED_RECIPIENTS:
            return PolicyResult(
                allowed=False,
                rejection_code=RejectionCode.DISALLOWED_RECIPIENT,
                rejection_text=(
                    f"REJECTED: pm cannot target {effective_target!r}. "
                    f"Allowed PM recipients: "
                    f"{sorted(PM_ALLOWED_RECIPIENTS)}."
                ),
            )

    # Non-PM senders must not target GitHub — only PM is authorised.
    if recipient_role == "github" and sender_role != "pm":
        return PolicyResult(
            allowed=False,
            rejection_code=RejectionCode.DISALLOWED_RECIPIENT,
            rejection_text=(
                f"REJECTED: only pm can target github, "
                f"got sender {sender_role!r}."
            ),
        )

    # Unsupported type
    if message_type not in ALLOWED_INBOUND_MESSAGE_TYPES:
        if message_type == "autonomous_follow_on":
            return PolicyResult(
                allowed=False,
                rejection_code=RejectionCode.AUTONOMOUS_FOLLOW_ON,
                rejection_text=("REJECTED: autonomous follow-on tasks not allowed."),
            )
        return PolicyResult(
            allowed=False,
            rejection_code=RejectionCode.UNSUPPORTED_TYPE,
            rejection_text=(
                f"REJECTED: unsupported message type {message_type!r}. "
                f"Allowed inbound: {sorted(ALLOWED_INBOUND_MESSAGE_TYPES)}."
            ),
        )

    # All checks passed
    return PolicyResult(allowed=True)
