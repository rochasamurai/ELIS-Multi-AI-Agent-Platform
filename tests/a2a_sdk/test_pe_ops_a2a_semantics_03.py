"""
PE-OPS-A2A-RUNTIME-LOOPBACK-01 — Gate 3 governed semantics validation
(includes Gate 2E policy + Gate 3 timestamp governance).

Validates the 32-row policy decision table for the Advisor ↔ Supervisor
loopback topology.  Assumes both servers are running on their canonical ports
(Advisor 9500, Supervisor 9501).

32 test cases:
  12 allowed → TASK_STATE_COMPLETED
  11 rejected (Gate 2E) → TASK_STATE_REJECTED
   4 timestamp unit tests (validate_timestamp directly)
   4 timestamp integration tests (live servers)
   1 PM destination denial unit test (DISALLOWED_RECIPIENT)

Run:
  cd /opt/elis/repo && PYTHONPATH=. /opt/elis/a2a/venv/bin/python \\
    tests/a2a_sdk/test_pe_ops_a2a_semantics_03.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from google.protobuf.json_format import MessageToDict
from google.protobuf.struct_pb2 import Struct

from a2a.client.card_resolver import A2ACardResolver
from a2a.client.client_factory import ClientFactory
from a2a.types import a2a_pb2
from a2a.utils.proto_utils import ParseDict

ADVISOR_URL = "http://127.0.0.1:9500"
SUPERVISOR_URL = "http://127.0.0.1:9501"

PASSES = 0
FAILS = 0


def pass_(label: str) -> None:
    global PASSES
    PASSES += 1
    print(f"  PASS: {label}")


def fail(label: str, detail: str = "") -> None:
    global FAILS
    FAILS += 1
    msg = f"  FAIL: {label}"
    if detail:
        msg += f"  |  {detail}"
    print(msg)


# ── Timestamp helpers ────────────────────────────────────────────────────────


def _utcnow_iso() -> str:
    """Return the current UTC time as an ISO 8601 string with ``Z`` suffix."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stale_timestamp(age_s: int = 600) -> str:
    """Return an ISO 8601 UTC timestamp *age_s* seconds in the past."""
    return (datetime.now(timezone.utc) - timedelta(seconds=age_s)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _future_timestamp(offset_s: int = 120) -> str:
    """Return an ISO 8601 UTC timestamp *offset_s* seconds in the future."""
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_s)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


# ── Client helpers ───────────────────────────────────────────────────────────


async def fetch_card(http: httpx.AsyncClient, base_url: str) -> a2a_pb2.AgentCard:
    """Fetch the Agent Card from *base_url*."""
    resolver = A2ACardResolver(http, base_url=base_url)
    return await resolver.get_agent_card()


async def send_governed_message(
    client,
    *,
    target_url: str,
    sender_role: str,
    message_type: str,
    text: str = "Gate 3 diagnostic message.",
    task_ref: Optional[str] = None,
    target_role: Optional[str] = None,
    elis_sent_at=None,  # type: ignore[assignment] — _NO_TS sentinel or str|None
) -> list[dict]:
    """Send a governed message with ELIS metadata and collect stream events.

    Args:
        target_role: If set, adds ``elis_target_role`` to metadata for
                     PM destination allowlist enforcement.
        elis_sent_at: ISO 8601 UTC timestamp.  If ``None``, the field is
                      **omitted entirely** (used for E_TS_MISSING tests).
                      If not provided at all, defaults to ``_utcnow_iso()``
                      for normal allowed/rejected traffic.
    """
    metadata = Struct()
    meta_dict: dict[str, str] = {
        "elis_sender_role": sender_role,
        "elis_message_type": message_type,
        "elis_policy_version": "1.0.0",
    }
    # Only add elis_sent_at if a value was explicitly provided or we default it.
    # We detect "not provided" by a special sentinel.
    if elis_sent_at is not _NO_TS:  # type: ignore[comparison-overlap]
        meta_dict["elis_sent_at"] = (
            elis_sent_at if elis_sent_at is not None else _utcnow_iso()
        )
    if task_ref:
        meta_dict["elis_task_ref"] = task_ref
    if target_role:
        meta_dict["elis_target_role"] = target_role
    metadata.update(meta_dict)

    part = ParseDict({"text": text}, a2a_pb2.Part())
    msg = ParseDict(
        {
            "message_id": str(uuid.uuid4()),
            "context_id": str(uuid.uuid4()),
            "role": a2a_pb2.Role.Value("ROLE_USER"),
            "metadata": MessageToDict(
                metadata,
                preserving_proto_field_name=True,
                always_print_fields_with_no_presence=False,
            ),
            "parts": [
                MessageToDict(
                    part,
                    preserving_proto_field_name=True,
                    always_print_fields_with_no_presence=False,
                )
            ],
        },
        a2a_pb2.Message(),
    )
    req = a2a_pb2.SendMessageRequest(message=msg)

    events = []
    async for resp in client.send_message(req):
        which = resp.WhichOneof("payload")
        event: dict[str, object] = {"type": which}
        if which == "task":
            t = resp.task
            state = a2a_pb2.TaskState.Name(t.status.state)
            event["task_id"] = t.id
            event["state"] = state
            if t.status.message:
                # Extract text from parts
                for p in t.status.message.parts:
                    if p.HasField("text"):
                        event["text"] = p.text
                # Extract metadata (rejection code)
                if t.status.message.metadata:
                    msg_meta = t.status.message.metadata
                    if "elis_rejection_code" in msg_meta:
                        event["rejection_code"] = msg_meta["elis_rejection_code"]
        elif which == "status_update":
            event["state"] = a2a_pb2.TaskState.Name(resp.status_update.state)
        events.append(event)
    return events


# Sentinel: when elis_sent_at is NOT passed to send_governed_message at all,
# we default to a fresh timestamp.  When the caller passes _NO_TS explicitly,
# we omit the field entirely (for E_TS_MISSING tests).
_NO_TS = object()


# ── Assertion helpers ────────────────────────────────────────────────────────


async def send_no_metadata(client, text: str = "No metadata message.") -> list[dict]:
    """Send a message WITHOUT any metadata field — malformed envelope test."""
    part = ParseDict({"text": text}, a2a_pb2.Part())
    msg = ParseDict(
        {
            "message_id": str(uuid.uuid4()),
            "context_id": str(uuid.uuid4()),
            "role": a2a_pb2.Role.Value("ROLE_USER"),
            # ── NO "metadata" key ──
            "parts": [
                MessageToDict(
                    part,
                    preserving_proto_field_name=True,
                    always_print_fields_with_no_presence=False,
                )
            ],
        },
        a2a_pb2.Message(),
    )
    req = a2a_pb2.SendMessageRequest(message=msg)

    events = []
    async for resp in client.send_message(req):
        which = resp.WhichOneof("payload")
        event: dict[str, object] = {"type": which}
        if which == "task":
            t = resp.task
            event["state"] = a2a_pb2.TaskState.Name(t.status.state)
            if t.status.message:
                for p in t.status.message.parts:
                    if p.HasField("text"):
                        event["text"] = p.text
                if t.status.message.metadata:
                    msg_meta = t.status.message.metadata
                    if "elis_rejection_code" in msg_meta:
                        event["rejection_code"] = msg_meta["elis_rejection_code"]
        events.append(event)
    return events


# ── Assertion helpers ────────────────────────────────────────────────────────


def assert_completed(events: list[dict], label: str) -> bool:
    """Assert the final event is TASK_STATE_COMPLETED."""
    final = events[-1] if events else {}
    if final.get("state") != "TASK_STATE_COMPLETED":
        fail(label, f"expected TASK_STATE_COMPLETED, got {final.get('state')}")
        return False
    pass_(label)
    return True


def assert_rejected(events: list[dict], expected_code: str, label: str) -> bool:
    """Assert TASK_STATE_REJECTED with the expected rejection code."""
    final = events[-1] if events else {}
    state = final.get("state")
    code = final.get("rejection_code")

    if state != "TASK_STATE_REJECTED":
        fail(label, f"expected TASK_STATE_REJECTED, got {state}")
        return False

    if code != expected_code:
        fail(
            label,
            f"expected rejection code {expected_code!r}, got {code!r}",
        )
        return False

    pass_(label)
    return True


def assert_no_rejection_code(events: list[dict], label: str) -> bool:
    """Assert the response has no rejection code (allowed message)."""
    for e in events:
        if e.get("rejection_code"):
            fail(
                label,
                f"unexpected rejection code in allowed message: "
                f"{e['rejection_code']!r}",
            )
            return False
    pass_(label)
    return True


# ── Main test ────────────────────────────────────────────────────────────────


async def main() -> int:
    global PASSES, FAILS

    print("=" * 60)
    print("Gate 3 — Governed A2A Semantics + Timestamp Governance")
    print("=" * 60)

    # ── Step 0: Fetch Agent Cards ──────────────────────────────────────
    print("\n── Step 0: Fetch Agent Cards ──")
    async with httpx.AsyncClient() as http:
        advisor_card = await fetch_card(http, ADVISOR_URL)
        supervisor_card = await fetch_card(http, SUPERVISOR_URL)

    assert (
        advisor_card.name == "ELIS Advisor"
    ), f"bad advisor card name: {advisor_card.name}"
    assert (
        supervisor_card.name == "ELIS Supervisor"
    ), f"bad supervisor card name: {supervisor_card.name}"
    pass_("Advisor Agent Card fetched")
    pass_("Supervisor Agent Card fetched")

    factory = ClientFactory()
    advisor_client = factory.create(advisor_card)
    supervisor_client = factory.create(supervisor_card)
    pass_("Both A2A clients instantiated")

    # ═══════════════════════════════════════════════════════════════════
    # ALLOWED CASES (rows 1–12): request, ack, status across roles
    # ═══════════════════════════════════════════════════════════════════

    print("\n── Allowed: Row 1 — advisor → supervisor request ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="advisor",
        message_type="request",
    )
    assert_completed(events, "Row 1: advisor→supervisor request → COMPLETED")
    assert_no_rejection_code(events, "Row 1: no rejection code")

    print("\n── Allowed: Row 2 — supervisor → advisor request ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="supervisor",
        message_type="request",
    )
    assert_completed(events, "Row 2: supervisor→advisor request → COMPLETED")
    assert_no_rejection_code(events, "Row 2: no rejection code")

    print("\n── Allowed: Row 3 — advisor → supervisor ack ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="advisor",
        message_type="ack",
    )
    assert_completed(events, "Row 3: advisor→supervisor ack → COMPLETED")
    assert_no_rejection_code(events, "Row 3: no rejection code")

    print("\n── Allowed: Row 4 — supervisor → advisor ack ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="supervisor",
        message_type="ack",
    )
    assert_completed(events, "Row 4: supervisor→advisor ack → COMPLETED")
    assert_no_rejection_code(events, "Row 4: no rejection code")

    print("\n── Allowed: Row 5 — advisor → supervisor status ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="advisor",
        message_type="status",
    )
    assert_completed(events, "Row 5: advisor→supervisor status → COMPLETED")
    assert_no_rejection_code(events, "Row 5: no rejection code")

    print("\n── Allowed: Row 6 — supervisor → advisor status ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="supervisor",
        message_type="status",
    )
    assert_completed(events, "Row 6: supervisor→advisor status → COMPLETED")
    assert_no_rejection_code(events, "Row 6: no rejection code")

    # ═══════════════════════════════════════════════════════════════════
    # ALLOWED CASES — PM sender enrolment (rows 7–12)
    # ═══════════════════════════════════════════════════════════════════

    print("\n── Allowed: Row 7 — pm → advisor request ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="pm",
        message_type="request",
    )
    assert_completed(events, "Row 7: pm→advisor request → COMPLETED")
    assert_no_rejection_code(events, "Row 7: no rejection code")

    print("\n── Allowed: Row 8 — pm → supervisor request ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="pm",
        message_type="request",
    )
    assert_completed(events, "Row 8: pm→supervisor request → COMPLETED")
    assert_no_rejection_code(events, "Row 8: no rejection code")

    print("\n── Allowed: Row 9 — pm → advisor ack ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="pm",
        message_type="ack",
    )
    assert_completed(events, "Row 9: pm→advisor ack → COMPLETED")
    assert_no_rejection_code(events, "Row 9: no rejection code")

    print("\n── Allowed: Row 10 — pm → supervisor ack ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="pm",
        message_type="ack",
    )
    assert_completed(events, "Row 10: pm→supervisor ack → COMPLETED")
    assert_no_rejection_code(events, "Row 10: no rejection code")

    print("\n── Allowed: Row 11 — pm → advisor status ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="pm",
        message_type="status",
    )
    assert_completed(events, "Row 11: pm→advisor status → COMPLETED")
    assert_no_rejection_code(events, "Row 11: no rejection code")

    print("\n── Allowed: Row 12 — pm → supervisor status ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="pm",
        message_type="status",
    )
    assert_completed(events, "Row 12: pm→supervisor status → COMPLETED")
    assert_no_rejection_code(events, "Row 12: no rejection code")

    # ═══════════════════════════════════════════════════════════════════
    # REJECTED CASES — Gate 2E (rows 13–23)
    # ═══════════════════════════════════════════════════════════════════

    # ── Rows 13–14: Self-target ──────────────────────────────────────────
    print("\n── Rejected: Row 13 — advisor → advisor (self-target) ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="advisor",
        message_type="request",
    )
    assert_rejected(
        events,
        "REJECTED_SELF_TARGET",
        "Row 13: advisor self-target → REJECTED_SELF_TARGET",
    )

    print("\n── Rejected: Row 14 — supervisor → supervisor (self-target) ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="supervisor",
        message_type="request",
    )
    assert_rejected(
        events,
        "REJECTED_SELF_TARGET",
        "Row 14: supervisor self-target → REJECTED_SELF_TARGET",
    )

    # ── Row 15: Malformed envelope (no metadata) ────────────────────────
    print("\n── Rejected: Row 15 — no metadata (malformed envelope) ──")
    events = await send_no_metadata(advisor_client)
    assert_rejected(
        events,
        "REJECTED_MALFORMED_ENVELOPE",
        "Row 15: no metadata → REJECTED_MALFORMED_ENVELOPE",
    )

    # ── Row 16: Unknown sender ─────────────────────────────────────────
    print("\n── Rejected: Row 16 — unknown sender ──")
    events = await send_governed_message(
        advisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="unknown_agent",
        message_type="request",
    )
    assert_rejected(
        events,
        "REJECTED_UNKNOWN_SENDER",
        "Row 16: unknown sender → REJECTED_UNKNOWN_SENDER",
    )

    # ── Rows 17–18: Unsupported type ───────────────────────────────────
    print("\n── Rejected: Row 17 — advisor→supervisor unsupported type ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="advisor",
        message_type="execute_command",
    )
    assert_rejected(
        events,
        "REJECTED_UNSUPPORTED_TYPE",
        "Row 17: unsupported type → REJECTED_UNSUPPORTED_TYPE",
    )

    print("\n── Rejected: Row 18 — supervisor→advisor unsupported type ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="supervisor",
        message_type="deploy_production",
    )
    assert_rejected(
        events,
        "REJECTED_UNSUPPORTED_TYPE",
        "Row 18: unsupported type → REJECTED_UNSUPPORTED_TYPE",
    )

    # ── Rows 19–20: Autonomous follow-on ───────────────────────────────
    print("\n── Rejected: Row 19 — advisor→supervisor autonomous_follow_on ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="advisor",
        message_type="autonomous_follow_on",
    )
    assert_rejected(
        events,
        "REJECTED_AUTONOMOUS_FOLLOW_ON",
        "Row 19: autonomous_follow_on → REJECTED_AUTONOMOUS_FOLLOW_ON",
    )

    print("\n── Rejected: Row 20 — supervisor→advisor autonomous_follow_on ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="supervisor",
        message_type="autonomous_follow_on",
    )
    assert_rejected(
        events,
        "REJECTED_AUTONOMOUS_FOLLOW_ON",
        "Row 20: autonomous_follow_on → REJECTED_AUTONOMOUS_FOLLOW_ON",
    )

    # ── Rows 21–22: PM rejected cases ───────────────────────────────────
    print("\n── Rejected: Row 21 — pm→advisor unsupported type ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="pm",
        message_type="execute_command",
    )
    assert_rejected(
        events,
        "REJECTED_UNSUPPORTED_TYPE",
        "Row 21: pm unsupported type → REJECTED_UNSUPPORTED_TYPE",
    )

    print("\n── Rejected: Row 22 — pm→supervisor autonomous_follow_on ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="pm",
        message_type="autonomous_follow_on",
    )
    assert_rejected(
        events,
        "REJECTED_AUTONOMOUS_FOLLOW_ON",
        "Row 22: pm autonomous_follow_on → REJECTED_AUTONOMOUS_FOLLOW_ON",
    )

    # ── Row 23: PM destination denial — policy unit test ──────────────
    print("\n── Rejected: Row 23 — pm→github policy unit test ──")
    from elis.a2a.policy import validate_message as vm, RejectionCode as RC

    result = vm(
        sender_role="pm",
        message_type="request",
        recipient_role="advisor",
        declared_target_role="github",
        elis_sent_at=_utcnow_iso(),
    )
    if not result.allowed and result.rejection_code == RC.DISALLOWED_RECIPIENT:
        pass_("Row 23: pm→github → REJECTED_DISALLOWED_RECIPIENT (unit)")
    else:
        fail(
            "Row 23: pm→github policy unit test",
            f"expected DISALLOWED_RECIPIENT, got "
            f"allowed={result.allowed} code={result.rejection_code!r}",
        )

    # ═══════════════════════════════════════════════════════════════════
    # GATE 3 — TIMESTAMP GOVERNANCE (rows 24–31)
    # ═══════════════════════════════════════════════════════════════════

    from elis.a2a.policy import validate_timestamp

    # ── Unit tests: validate_timestamp() directly ──────────────────────
    print("\n── Timestamp unit: E_TS_MISSING ──")
    result = validate_timestamp(elis_sent_at=None)
    if not result.allowed and result.rejection_code == RC.TS_MISSING:
        pass_("Row 24: E_TS_MISSING — None timestamp (unit)")
    else:
        fail(
            "Row 24: E_TS_MISSING unit",
            f"expected TS_MISSING, got allowed={result.allowed} "
            f"code={result.rejection_code!r}",
        )

    print("\n── Timestamp unit: E_TS_MALFORMED ──")
    result = validate_timestamp(elis_sent_at="not-a-timestamp")
    if not result.allowed and result.rejection_code == RC.TS_MALFORMED:
        pass_("Row 25: E_TS_MALFORMED — garbage timestamp (unit)")
    else:
        fail(
            "Row 25: E_TS_MALFORMED unit",
            f"expected TS_MALFORMED, got allowed={result.allowed} "
            f"code={result.rejection_code!r}",
        )

    print("\n── Timestamp unit: E_TS_STALE ──")
    result = validate_timestamp(elis_sent_at=_stale_timestamp(age_s=600))
    if not result.allowed and result.rejection_code == RC.TS_STALE:
        pass_("Row 26: E_TS_STALE — 600s old timestamp (unit)")
    else:
        fail(
            "Row 26: E_TS_STALE unit",
            f"expected TS_STALE, got allowed={result.allowed} "
            f"code={result.rejection_code!r}",
        )

    print("\n── Timestamp unit: E_TS_FUTURE ──")
    result = validate_timestamp(elis_sent_at=_future_timestamp(offset_s=120))
    if not result.allowed and result.rejection_code == RC.TS_FUTURE:
        pass_("Row 27: E_TS_FUTURE — 120s future timestamp (unit)")
    else:
        fail(
            "Row 27: E_TS_FUTURE unit",
            f"expected TS_FUTURE, got allowed={result.allowed} "
            f"code={result.rejection_code!r}",
        )

    print("\n── Timestamp unit: valid timestamp (acceptance) ──")
    result = validate_timestamp(elis_sent_at=_utcnow_iso())
    if result.allowed:
        pass_("Row 28: valid timestamp → allowed (unit)")
    else:
        fail(
            "Row 28: valid timestamp acceptance",
            f"expected allowed=True, got code={result.rejection_code!r}",
        )

    # ── Integration tests: live servers with bad timestamps ────────────
    print("\n── Timestamp integration: E_TS_MISSING (no elis_sent_at) ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="supervisor",
        message_type="request",
        elis_sent_at=_NO_TS,
    )
    assert_rejected(
        events,
        "E_TS_MISSING",
        "Row 29: no elis_sent_at → E_TS_MISSING (integration)",
    )

    print("\n── Timestamp integration: E_TS_MALFORMED (garbage) ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="supervisor",
        message_type="request",
        elis_sent_at="garbage-not-iso",
    )
    assert_rejected(
        events,
        "E_TS_MALFORMED",
        "Row 30: malformed timestamp → E_TS_MALFORMED (integration)",
    )

    print("\n── Timestamp integration: E_TS_STALE (old timestamp) ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="supervisor",
        message_type="request",
        elis_sent_at=_stale_timestamp(age_s=600),
    )
    assert_rejected(
        events,
        "E_TS_STALE",
        "Row 31: stale timestamp → E_TS_STALE (integration)",
    )

    print("\n── Timestamp integration: E_TS_FUTURE (far future) ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="supervisor",
        message_type="request",
        elis_sent_at=_future_timestamp(offset_s=120),
    )
    assert_rejected(
        events,
        "E_TS_FUTURE",
        "Row 32: future timestamp → E_TS_FUTURE (integration)",
    )

    # ═══════════════════════════════════════════════════════════════════
    # RESULT
    # ═══════════════════════════════════════════════════════════════════
    print(f"\n{'=' * 60}")
    total = PASSES + FAILS
    print(f"RESULTS: {PASSES}/{total} passed, {FAILS} failed")
    if FAILS == 0:
        print("VERDICT: PASS")
        return 0
    else:
        print("VERDICT: FAIL")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))