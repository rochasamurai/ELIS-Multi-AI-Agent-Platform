"""
ELIS Local A2A Transport Layer — PE-OPS-A2A-RUNTIME-01

This module provides a purely local, file-based message transport so ELIS agents can
exchange structured messages without Discord routing.  Discord remains the PO-facing
channel.

GOVERNANCE BOUNDARY (non-negotiable):
  - This layer carries NO governance authority.
  - This layer carries NO merge authority.
  - This layer does NOT bypass PO approval.
  - This layer does NOT bypass implementer/validator gate checks.
  - This layer does NOT replace PE evidence requirements.
  - Messages exchanged here are internal coordination signals only.

Transport mechanics:
  - Mailbox root: /opt/elis/a2a/mailboxes/
  - Each message is written as a single JSON file: <mailbox_root>/<recipient>/<message_id>.json
  - No sockets, no HTTP, no network calls of any kind.
  - Schema validation uses jsonschema when available; falls back to required-field check.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "a2a_message.schema.json"
_A2A_RUNTIME_ROOT = Path("/opt/elis/a2a")
_MAILBOX_ROOT = _A2A_RUNTIME_ROOT / "mailboxes"
_ENABLED_SENTINEL = _A2A_RUNTIME_ROOT / ".enabled"


class A2ATransportDisabledError(RuntimeError):
    """Raised when the ELIS A2A transport is used before it has been enabled."""


_VALID_MESSAGE_TYPES = frozenset(
    ["status", "reset_ack", "task_state", "evidence_ref", "failure"]
)

# ---------------------------------------------------------------------------
# Schema validator (jsonschema if available, else minimal built-in check)
# ---------------------------------------------------------------------------

try:
    import jsonschema  # type: ignore

    _SCHEMA: Optional[dict] = None

    def _load_schema() -> dict:
        global _SCHEMA
        if _SCHEMA is None:
            with open(_SCHEMA_PATH) as fh:
                _SCHEMA = json.load(fh)
        return _SCHEMA

    def _validate_envelope(data: dict) -> None:
        jsonschema.validate(instance=data, schema=_load_schema())

except ImportError:  # pragma: no cover — jsonschema missing; use built-in fallback

    def _validate_envelope(data: dict) -> None:  # type: ignore[misc]
        required = {
            "message_id",
            "sender",
            "recipient",
            "message_type",
            "payload",
            "timestamp",
        }
        missing = required - data.keys()
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
        if data["message_type"] not in _VALID_MESSAGE_TYPES:
            raise ValueError(
                f"Invalid message_type '{data['message_type']}'. "
                f"Must be one of: {sorted(_VALID_MESSAGE_TYPES)}"
            )
        if not isinstance(data["payload"], dict):
            raise ValueError("payload must be an object (dict)")


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class A2AMessage:
    """Structured message envelope for the ELIS local A2A transport layer."""

    sender: str
    recipient: str
    message_type: str
    payload: dict = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    pe_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "message_id": self.message_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "message_type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }
        if self.pe_id is not None:
            d["pe_id"] = self.pe_id
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "A2AMessage":
        return cls(
            message_id=data["message_id"],
            sender=data["sender"],
            recipient=data["recipient"],
            message_type=data["message_type"],
            payload=data["payload"],
            timestamp=data["timestamp"],
            pe_id=data.get("pe_id"),
        )


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------


class A2ATransport:
    """
    File-based local A2A message transport.

    Governance boundaries:
      - No governance authority.
      - No merge authority.
      - Does not bypass PO approval or gate checks.
      - Does not replace PE evidence requirements.
    """

    # Explicit absence of governance/merge authority attributes is testable.
    has_governance_authority: bool = False
    has_merge_authority: bool = False
    can_bypass_po_approval: bool = False
    can_bypass_gate_checks: bool = False

    def __init__(
        self,
        mailbox_root: Path = _MAILBOX_ROOT,
        *,
        skip_enabled_check: bool = False,
    ) -> None:
        self._root = Path(mailbox_root)
        if not skip_enabled_check and not _ENABLED_SENTINEL.exists():
            raise A2ATransportDisabledError(
                f"ELIS A2A transport is disabled. "
                f"Enable marker not found: {_ENABLED_SENTINEL}"
            )

    def _mailbox(self, recipient: str) -> Path:
        inbox = self._root / recipient / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        (self._root / recipient / "processed").mkdir(parents=True, exist_ok=True)
        (self._root / recipient / "dead").mkdir(parents=True, exist_ok=True)
        return inbox

    def send(self, message: A2AMessage) -> Path:
        """
        Validate and deliver a message to the recipient's mailbox.

        Returns the path of the written message file.
        Raises ValueError (or jsonschema.ValidationError) on invalid envelopes.
        """
        envelope = message.to_dict()
        _validate_envelope(envelope)
        dest = self._mailbox(message.recipient) / f"{message.message_id}.json"
        dest.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
        return dest

    def receive(self, recipient: str) -> list[A2AMessage]:
        """
        Return all pending messages from the recipient's inbox and move them
        to processed/. Corrupt files are moved to dead/.
        """
        inbox = self._root / recipient / "inbox"
        if not inbox.is_dir():
            return []
        processed = self._root / recipient / "processed"
        dead = self._root / recipient / "dead"
        processed.mkdir(parents=True, exist_ok=True)
        dead.mkdir(parents=True, exist_ok=True)
        messages: list[A2AMessage] = []
        for path in sorted(inbox.iterdir()):
            if path.suffix != ".json":
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                messages.append(A2AMessage.from_dict(data))
                path.rename(processed / path.name)
            except (json.JSONDecodeError, KeyError):
                path.rename(dead / path.name)
        return messages

    def list_messages(self, recipient: str) -> list[A2AMessage]:
        """
        Return all pending messages from the recipient's inbox WITHOUT removing them.
        """
        inbox = self._root / recipient / "inbox"
        if not inbox.is_dir():
            return []
        messages: list[A2AMessage] = []
        for path in sorted(inbox.iterdir()):
            if path.suffix != ".json":
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                messages.append(A2AMessage.from_dict(data))
            except (json.JSONDecodeError, KeyError):
                pass
        return messages
