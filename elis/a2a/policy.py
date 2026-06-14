"""
ELIS A2A governed message semantics — shared policy module.

Gate 2E: validates sender role, recipient role, and message type
against the approved Advisor ↔ Supervisor loopback policy table.

Inbound message types: request, ack, status.
policy_rejection is outbound-only — produced by TaskUpdater.reject().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

ALLOWED_SENDER_ROLES = frozenset({"advisor", "supervisor"})
ALLOWED_INBOUND_MESSAGE_TYPES = frozenset({"request", "ack", "status"})


class RejectionCode:
    SELF_TARGET = "REJECTED_SELF_TARGET"
    MALFORMED_ENVELOPE = "REJECTED_MALFORMED_ENVELOPE"
    UNKNOWN_SENDER = "REJECTED_UNKNOWN_SENDER"
    UNSUPPORTED_TYPE = "REJECTED_UNSUPPORTED_TYPE"
    AUTONOMOUS_FOLLOW_ON = "REJECTED_AUTONOMOUS_FOLLOW_ON"


@dataclass(frozen=True)
class PolicyResult:
    allowed: bool
    rejection_code: Optional[str] = None
    rejection_text: Optional[str] = None


def validate_message(
    *,
    sender_role: Optional[str],
    message_type: Optional[str],
    recipient_role: str,
) -> PolicyResult:
    """Validate an incoming message against the Gate 2E policy table.

    Args:
        sender_role: Value of Message.metadata.elis_sender_role.
        message_type: Value of Message.metadata.elis_message_type.
        recipient_role: The role of the agent receiving the message
                        ("advisor" or "supervisor").

    Returns:
        PolicyResult with allowed=True/False and rejection details if denied.
    """
    # Malformed: missing metadata
    if sender_role is None or message_type is None:
        return PolicyResult(
            allowed=False,
            rejection_code=RejectionCode.MALFORMED_ENVELOPE,
            rejection_text="REJECTED: missing required metadata fields "
            "(elis_sender_role, elis_message_type).",
        )

    # Unknown sender
    if sender_role not in ALLOWED_SENDER_ROLES:
        return PolicyResult(
            allowed=False,
            rejection_code=RejectionCode.UNKNOWN_SENDER,
            rejection_text=f"REJECTED: unknown sender role {sender_role!r}. "
            f"Allowed: {sorted(ALLOWED_SENDER_ROLES)}.",
        )

    # Self-target
    if sender_role == recipient_role:
        return PolicyResult(
            allowed=False,
            rejection_code=RejectionCode.SELF_TARGET,
            rejection_text=f"REJECTED: self-target not allowed "
            f"({sender_role} → {recipient_role}).",
        )

    # Unsupported type
    if message_type not in ALLOWED_INBOUND_MESSAGE_TYPES:
        if message_type == "autonomous_follow_on":
            return PolicyResult(
                allowed=False,
                rejection_code=RejectionCode.AUTONOMOUS_FOLLOW_ON,
                rejection_text="REJECTED: autonomous follow-on tasks not allowed.",
            )
        return PolicyResult(
            allowed=False,
            rejection_code=RejectionCode.UNSUPPORTED_TYPE,
            rejection_text=f"REJECTED: unsupported message type {message_type!r}. "
            f"Allowed inbound: {sorted(ALLOWED_INBOUND_MESSAGE_TYPES)}.",
        )

    # All checks passed
    return PolicyResult(allowed=True)
