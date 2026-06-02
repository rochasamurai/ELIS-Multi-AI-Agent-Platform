"""
Pytest suite for scripts/a2a_local_transport.py — PE-OPS-A2A-RUNTIME-01

Covers:
  - Schema validation (valid and invalid envelopes)
  - Round-trip smoke test: 'pm' sends to 'supervisor', 'supervisor' receives, content matches
  - One test per message_type (status, reset_ack, task_state, evidence_ref, failure)
  - Governance/merge authority assertion (transport must carry no such attributes)
  - list_messages (non-destructive read)
  - broadcast recipient
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Allow importing from scripts/ without installing the package.
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from a2a_local_transport import A2AMessage, A2ATransport  # noqa: E402

import importlib.util

_HAS_JSONSCHEMA = importlib.util.find_spec("jsonschema") is not None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def transport(tmp_path):
    """Return an A2ATransport backed by a temporary directory (sentinel check bypassed)."""
    return A2ATransport(mailbox_root=tmp_path, skip_enabled_check=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _valid_envelope(**overrides) -> dict:
    base = {
        "message_id": str(uuid.uuid4()),
        "sender": "pm",
        "recipient": "supervisor",
        "message_type": "status",
        "payload": {"text": "all good"},
        "timestamp": _now_iso(),
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Schema validation — valid envelopes
# ---------------------------------------------------------------------------


class TestSchemaValid:
    def test_minimal_valid_envelope(self, transport):
        msg = A2AMessage(
            sender="pm",
            recipient="supervisor",
            message_type="status",
            payload={"state": "implementing"},
        )
        written = transport.send(msg)
        assert written.exists()

    def test_envelope_with_pe_id(self, transport):
        msg = A2AMessage(
            sender="advisor",
            recipient="pm",
            message_type="task_state",
            payload={"pe": "PE-OPS-A2A-RUNTIME-01"},
            pe_id="PE-OPS-A2A-RUNTIME-01",
        )
        transport.send(msg)
        received = transport.receive("pm")
        assert len(received) == 1
        assert received[0].pe_id == "PE-OPS-A2A-RUNTIME-01"

    def test_broadcast_recipient_accepted(self, transport):
        msg = A2AMessage(
            sender="pm",
            recipient="broadcast",
            message_type="status",
            payload={},
        )
        transport.send(msg)
        received = transport.receive("broadcast")
        assert len(received) == 1


# ---------------------------------------------------------------------------
# Schema validation — invalid envelopes
# ---------------------------------------------------------------------------


class TestSchemaInvalid:
    def test_missing_message_id(self, transport):
        msg = A2AMessage(
            sender="pm",
            recipient="supervisor",
            message_type="status",
            payload={},
        )
        d = msg.to_dict()
        del d["message_id"]

        if _HAS_JSONSCHEMA:
            import jsonschema

            schema_path = (
                Path(__file__).parent.parent / "schemas" / "a2a_message.schema.json"
            )
            schema = json.loads(schema_path.read_text())
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(instance=d, schema=schema)
        else:
            from a2a_local_transport import _validate_envelope

            with pytest.raises(ValueError, match="message_id"):
                _validate_envelope(d)

    def test_invalid_message_type(self, transport):
        msg = A2AMessage(
            sender="pm",
            recipient="supervisor",
            message_type="status",
            payload={},
        )
        d = msg.to_dict()
        d["message_type"] = "governance_override"  # must be rejected

        if _HAS_JSONSCHEMA:
            import jsonschema

            schema_path = (
                Path(__file__).parent.parent / "schemas" / "a2a_message.schema.json"
            )
            schema = json.loads(schema_path.read_text())
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(instance=d, schema=schema)
        else:
            from a2a_local_transport import _validate_envelope

            with pytest.raises(ValueError, match="message_type"):
                _validate_envelope(d)

    def test_missing_sender(self, transport):
        msg = A2AMessage(
            sender="pm",
            recipient="supervisor",
            message_type="status",
            payload={},
        )
        d = msg.to_dict()
        del d["sender"]

        if _HAS_JSONSCHEMA:
            import jsonschema

            schema_path = (
                Path(__file__).parent.parent / "schemas" / "a2a_message.schema.json"
            )
            schema = json.loads(schema_path.read_text())
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(instance=d, schema=schema)
        else:
            from a2a_local_transport import _validate_envelope

            with pytest.raises(ValueError, match="sender"):
                _validate_envelope(d)

    def test_payload_must_be_object(self):
        from a2a_local_transport import _validate_envelope

        d = _valid_envelope(payload="not-an-object")
        if _HAS_JSONSCHEMA:
            import jsonschema

            schema_path = (
                Path(__file__).parent.parent / "schemas" / "a2a_message.schema.json"
            )
            schema = json.loads(schema_path.read_text())
            with pytest.raises(jsonschema.ValidationError):
                jsonschema.validate(instance=d, schema=schema)
        else:
            with pytest.raises(ValueError, match="payload"):
                _validate_envelope(d)


# ---------------------------------------------------------------------------
# Round-trip smoke test (AC-9)
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_pm_sends_to_supervisor_receives(self, transport):
        original = A2AMessage(
            sender="pm",
            recipient="supervisor",
            message_type="status",
            payload={"state": "gate-1-pending", "pe_id": "PE-OPS-A2A-RUNTIME-01"},
            pe_id="PE-OPS-A2A-RUNTIME-01",
        )
        transport.send(original)

        received = transport.receive("supervisor")

        assert len(received) == 1
        msg = received[0]
        assert msg.message_id == original.message_id
        assert msg.sender == "pm"
        assert msg.recipient == "supervisor"
        assert msg.message_type == "status"
        assert msg.payload["state"] == "gate-1-pending"
        assert msg.pe_id == "PE-OPS-A2A-RUNTIME-01"

    def test_receive_empties_mailbox(self, transport):
        msg = A2AMessage(
            sender="pm", recipient="supervisor", message_type="status", payload={}
        )
        transport.send(msg)
        first = transport.receive("supervisor")
        second = transport.receive("supervisor")
        assert len(first) == 1
        assert len(second) == 0

    def test_empty_mailbox_returns_empty_list(self, transport):
        result = transport.receive("nobody")
        assert result == []


# ---------------------------------------------------------------------------
# One test per message type
# ---------------------------------------------------------------------------


class TestMessageTypes:
    @pytest.mark.parametrize(
        "mtype", ["status", "reset_ack", "task_state", "evidence_ref", "failure"]
    )
    def test_each_message_type_round_trips(self, transport, mtype):
        msg = A2AMessage(
            sender="pm",
            recipient="supervisor",
            message_type=mtype,
            payload={"type_under_test": mtype},
        )
        transport.send(msg)
        received = transport.receive("supervisor")
        assert len(received) == 1
        assert received[0].message_type == mtype
        assert received[0].payload["type_under_test"] == mtype

    def test_status_carries_state_field(self, transport):
        msg = A2AMessage(
            sender="pm",
            recipient="advisor",
            message_type="status",
            payload={"state": "implementing"},
        )
        transport.send(msg)
        received = transport.receive("advisor")
        assert received[0].payload["state"] == "implementing"

    def test_reset_ack_carries_ack_field(self, transport):
        msg = A2AMessage(
            sender="supervisor",
            recipient="pm",
            message_type="reset_ack",
            payload={"ack": True, "reset_id": str(uuid.uuid4())},
        )
        transport.send(msg)
        received = transport.receive("pm")
        assert received[0].payload["ack"] is True

    def test_task_state_carries_task_id(self, transport):
        msg = A2AMessage(
            sender="pm",
            recipient="supervisor",
            message_type="task_state",
            payload={"task_id": "PE-OPS-A2A-RUNTIME-01", "state": "in-progress"},
        )
        transport.send(msg)
        received = transport.receive("supervisor")
        assert received[0].payload["task_id"] == "PE-OPS-A2A-RUNTIME-01"

    def test_evidence_ref_carries_path(self, transport):
        msg = A2AMessage(
            sender="advisor",
            recipient="pm",
            message_type="evidence_ref",
            payload={"ref": "docs/governance/ELIS_A2A_Runtime_Spec.md"},
        )
        transport.send(msg)
        received = transport.receive("pm")
        assert "docs/governance" in received[0].payload["ref"]

    def test_failure_carries_reason(self, transport):
        msg = A2AMessage(
            sender="supervisor",
            recipient="pm",
            message_type="failure",
            payload={"reason": "scope gate failed", "pe_id": "PE-X"},
        )
        transport.send(msg)
        received = transport.receive("pm")
        assert received[0].payload["reason"] == "scope gate failed"


# ---------------------------------------------------------------------------
# Governance / merge authority assertion (AC-3, AC-4)
# ---------------------------------------------------------------------------


class TestGovernanceBoundary:
    def test_transport_has_no_governance_authority(self, tmp_path):
        t = A2ATransport(mailbox_root=tmp_path, skip_enabled_check=True)
        assert t.has_governance_authority is False

    def test_transport_has_no_merge_authority(self, tmp_path):
        t = A2ATransport(mailbox_root=tmp_path, skip_enabled_check=True)
        assert t.has_merge_authority is False

    def test_transport_cannot_bypass_po_approval(self, tmp_path):
        t = A2ATransport(mailbox_root=tmp_path, skip_enabled_check=True)
        assert t.can_bypass_po_approval is False

    def test_transport_cannot_bypass_gate_checks(self, tmp_path):
        t = A2ATransport(mailbox_root=tmp_path, skip_enabled_check=True)
        assert t.can_bypass_gate_checks is False

    def test_transport_has_no_approve_method(self, tmp_path):
        t = A2ATransport(mailbox_root=tmp_path, skip_enabled_check=True)
        assert not hasattr(t, "approve")

    def test_transport_has_no_merge_method(self, tmp_path):
        t = A2ATransport(mailbox_root=tmp_path, skip_enabled_check=True)
        assert not hasattr(t, "merge")

    def test_transport_has_no_grant_authority_method(self, tmp_path):
        t = A2ATransport(mailbox_root=tmp_path, skip_enabled_check=True)
        assert not hasattr(t, "grant_authority")


# ---------------------------------------------------------------------------
# list_messages (non-destructive)
# ---------------------------------------------------------------------------


class TestListMessages:
    def test_list_does_not_remove_messages(self, transport):
        msg = A2AMessage(
            sender="pm", recipient="supervisor", message_type="status", payload={}
        )
        transport.send(msg)
        listed = transport.list_messages("supervisor")
        still_there = transport.list_messages("supervisor")
        assert len(listed) == 1
        assert len(still_there) == 1

    def test_list_empty_returns_empty(self, transport):
        assert transport.list_messages("nobody") == []

    def test_list_then_receive_consistent(self, transport):
        msg = A2AMessage(
            sender="pm",
            recipient="supervisor",
            message_type="task_state",
            payload={"x": 1},
        )
        transport.send(msg)
        listed = transport.list_messages("supervisor")
        received = transport.receive("supervisor")
        assert listed[0].message_id == received[0].message_id


# ---------------------------------------------------------------------------
# Gate 2A: enabled sentinel check
# ---------------------------------------------------------------------------


class TestGate2AEnabledSentinel:
    def test_transport_raises_when_sentinel_absent(self, tmp_path):
        import a2a_local_transport as mod
        from a2a_local_transport import A2ATransportDisabledError

        original = mod._ENABLED_SENTINEL
        mod._ENABLED_SENTINEL = tmp_path / ".enabled"
        try:
            with pytest.raises(A2ATransportDisabledError, match="disabled"):
                A2ATransport(mailbox_root=tmp_path)
        finally:
            mod._ENABLED_SENTINEL = original

    def test_transport_succeeds_when_sentinel_present(self, tmp_path):
        import a2a_local_transport as mod

        original = mod._ENABLED_SENTINEL
        sentinel = tmp_path / ".enabled"
        mod._ENABLED_SENTINEL = sentinel
        try:
            sentinel.touch()
            t = A2ATransport(mailbox_root=tmp_path)
            assert t is not None
        finally:
            mod._ENABLED_SENTINEL = original
            sentinel.unlink(missing_ok=True)

    def test_skip_enabled_check_bypasses_sentinel(self, tmp_path):
        t = A2ATransport(mailbox_root=tmp_path, skip_enabled_check=True)
        assert t is not None


# ---------------------------------------------------------------------------
# Gate 2A: inbox/processed/dead mailbox structure
# ---------------------------------------------------------------------------


class TestGate2AMailboxStructure:
    def test_send_writes_to_inbox(self, transport, tmp_path):
        msg = A2AMessage(
            sender="pm", recipient="infra-impl-a", message_type="status", payload={}
        )
        transport.send(msg)
        inbox = tmp_path / "infra-impl-a" / "inbox"
        assert inbox.is_dir()
        files = list(inbox.glob("*.json"))
        assert len(files) == 1

    def test_receive_moves_to_processed(self, transport, tmp_path):
        msg = A2AMessage(
            sender="pm", recipient="infra-val-b", message_type="status", payload={}
        )
        transport.send(msg)
        transport.receive("infra-val-b")
        inbox = tmp_path / "infra-val-b" / "inbox"
        processed = tmp_path / "infra-val-b" / "processed"
        assert len(list(inbox.glob("*.json"))) == 0
        assert len(list(processed.glob("*.json"))) == 1

    def test_corrupt_file_moves_to_dead(self, transport, tmp_path):
        inbox = tmp_path / "infra-impl-b" / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        corrupt = inbox / "corrupt.json"
        corrupt.write_text("{not valid json", encoding="utf-8")
        transport.receive("infra-impl-b")
        dead = tmp_path / "infra-impl-b" / "dead"
        assert (dead / "corrupt.json").exists()
        assert not corrupt.exists()

    def test_list_messages_reads_inbox_only(self, transport, tmp_path):
        msg = A2AMessage(
            sender="pm", recipient="infra-val-a", message_type="status", payload={}
        )
        transport.send(msg)
        listed = transport.list_messages("infra-val-a")
        assert len(listed) == 1
        inbox = tmp_path / "infra-val-a" / "inbox"
        assert len(list(inbox.glob("*.json"))) == 1

    def test_dead_dir_created_on_first_receive(self, transport, tmp_path):
        # No crash on empty mailbox receive
        result = transport.receive("infra-impl-a")
        assert result == []


# ---------------------------------------------------------------------------
# Gate 2A: Phase 1 ELIS agent identity smoke round-trips
# ---------------------------------------------------------------------------

PHASE_1_AGENTS = ["pm", "infra-impl-a", "infra-impl-b", "infra-val-a", "infra-val-b"]


class TestGate2APhase1AgentIds:
    @pytest.mark.parametrize("recipient", PHASE_1_AGENTS)
    def test_send_receive_for_phase1_agent(self, transport, recipient):
        msg = A2AMessage(
            sender="pm",
            recipient=recipient,
            message_type="status",
            payload={"gate": "2a"},
            pe_id="PE-OPS-A2A-PRODUCTION-02",
        )
        transport.send(msg)
        received = transport.receive(recipient)
        assert len(received) == 1
        assert received[0].recipient == recipient
        assert received[0].pe_id == "PE-OPS-A2A-PRODUCTION-02"
