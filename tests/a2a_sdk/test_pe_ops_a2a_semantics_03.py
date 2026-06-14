"""
PE-OPS-A2A-PRODUCTION-01 — Gate 2E governed semantics validation.

Validates the 14-row policy decision table for the Advisor ↔ Supervisor
loopback topology.  Assumes both servers are running on their canonical ports
(Advisor 9500, Supervisor 9501).

14 test cases:
  6 allowed  → TASK_STATE_COMPLETED
  8 rejected → TASK_STATE_REJECTED with correct REJECTED_* code in metadata

Run:
  cd /opt/elis/repo && PYTHONPATH=. /opt/elis/a2a/venv/bin/python \\
    tests/a2a_sdk/test_pe_ops_a2a_semantics_03.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
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


# ── Client helpers ─────────────────────────────────────────────────────────────


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
    text: str = "Gate 2E diagnostic message.",
    task_ref: Optional[str] = None,
) -> list[dict]:
    """Send a governed message with ELIS metadata and collect stream events."""
    metadata = Struct()
    meta_dict: dict[str, str] = {
        "elis_sender_role": sender_role,
        "elis_message_type": message_type,
        "elis_policy_version": "1.0.0",
    }
    if task_ref:
        meta_dict["elis_task_ref"] = task_ref
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


# ── Assertion helpers ──────────────────────────────────────────────────────────


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


# ── Main test ──────────────────────────────────────────────────────────────────


async def main() -> int:
    global PASSES, FAILS

    print("=" * 60)
    print("Gate 2E — Governed A2A Semantics Validation")
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
    # ALLOWED CASES (rows 1–6): request, ack, status across roles
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
    # REJECTED CASES (rows 7–14)
    # ═══════════════════════════════════════════════════════════════════

    # ── Rows 7–8: Self-target ──────────────────────────────────────────
    print("\n── Rejected: Row 7 — advisor → advisor (self-target) ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="advisor",
        message_type="request",
    )
    assert_rejected(
        events,
        "REJECTED_SELF_TARGET",
        "Row 7: advisor self-target → REJECTED_SELF_TARGET",
    )

    print("\n── Rejected: Row 8 — supervisor → supervisor (self-target) ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="supervisor",
        message_type="request",
    )
    assert_rejected(
        events,
        "REJECTED_SELF_TARGET",
        "Row 8: supervisor self-target → REJECTED_SELF_TARGET",
    )

    # ── Row 9: Malformed envelope (no metadata) ────────────────────────
    print("\n── Rejected: Row 9 — no metadata (malformed envelope) ──")
    events = await send_no_metadata(advisor_client)
    assert_rejected(
        events,
        "REJECTED_MALFORMED_ENVELOPE",
        "Row 9: no metadata → REJECTED_MALFORMED_ENVELOPE",
    )

    # ── Row 10: Unknown sender ─────────────────────────────────────────
    print("\n── Rejected: Row 10 — unknown sender ──")
    events = await send_governed_message(
        advisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="unknown_agent",
        message_type="request",
    )
    assert_rejected(
        events,
        "REJECTED_UNKNOWN_SENDER",
        "Row 10: unknown sender → REJECTED_UNKNOWN_SENDER",
    )

    # ── Rows 11–12: Unsupported type ───────────────────────────────────
    print("\n── Rejected: Row 11 — advisor→supervisor unsupported type ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="advisor",
        message_type="execute_command",
    )
    assert_rejected(
        events,
        "REJECTED_UNSUPPORTED_TYPE",
        "Row 11: unsupported type → REJECTED_UNSUPPORTED_TYPE",
    )

    print("\n── Rejected: Row 12 — supervisor→advisor unsupported type ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="supervisor",
        message_type="deploy_production",
    )
    assert_rejected(
        events,
        "REJECTED_UNSUPPORTED_TYPE",
        "Row 12: unsupported type → REJECTED_UNSUPPORTED_TYPE",
    )

    # ── Rows 13–14: Autonomous follow-on ───────────────────────────────
    print("\n── Rejected: Row 13 — advisor→supervisor autonomous_follow_on ──")
    events = await send_governed_message(
        supervisor_client,
        target_url=SUPERVISOR_URL,
        sender_role="advisor",
        message_type="autonomous_follow_on",
    )
    assert_rejected(
        events,
        "REJECTED_AUTONOMOUS_FOLLOW_ON",
        "Row 13: autonomous_follow_on → REJECTED_AUTONOMOUS_FOLLOW_ON",
    )

    print("\n── Rejected: Row 14 — supervisor→advisor autonomous_follow_on ──")
    events = await send_governed_message(
        advisor_client,
        target_url=ADVISOR_URL,
        sender_role="supervisor",
        message_type="autonomous_follow_on",
    )
    assert_rejected(
        events,
        "REJECTED_AUTONOMOUS_FOLLOW_ON",
        "Row 14: autonomous_follow_on → REJECTED_AUTONOMOUS_FOLLOW_ON",
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
