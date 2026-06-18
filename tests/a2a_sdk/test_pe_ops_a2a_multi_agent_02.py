"""
PE-OPS-A2A-PRODUCTION-01 — Gate 2C multi-agent smoke test.

Validates:
  1. Both Advisor (9500) and Supervisor (9501) serve valid Agent Cards
  2. Both cards resolve to distinct identities
  3. Official SDK clients can be instantiated from both cards
  4. A diagnostic task/message sent to each endpoint completes successfully
  5. Each response identifies the correct agent
  6. No cross-port identity confusion
"""

import asyncio
import sys
import uuid
from datetime import datetime, timezone

import httpx
from google.protobuf.struct_pb2 import Struct

from a2a.client.card_resolver import A2ACardResolver
from a2a.client.client_factory import ClientFactory
from a2a.types import a2a_pb2
from a2a.utils.proto_utils import ParseDict
from google.protobuf.json_format import MessageToDict

ADVISOR_URL = "http://127.0.0.1:9500"
SUPERVISOR_URL = "http://127.0.0.1:9501"


async def fetch_card(http, base_url):
    """Fetch the Agent Card from *base_url* via the well-known endpoint."""
    resolver = A2ACardResolver(http, base_url=base_url)
    return await resolver.get_agent_card()


async def send_message_and_collect(client, text):
    """Send a diagnostic message and collect all stream events.

    Args:
        client: A concrete Client returned by ClientFactory.create(card).
        text: The diagnostic message text to send.

    Returns:
        A list of event dicts with keys ``type``, ``task_id``, ``state``,
        and ``text`` (when present).
    """
    part = ParseDict({"text": text}, a2a_pb2.Part())
    metadata = Struct()
    metadata.update(
        {
            "elis_sender_role": "pm",
            "elis_message_type": "request",
            "elis_policy_version": "1.0.0",
            "elis_sent_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )
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
        event = {"type": which}
        if which == "task":
            t = resp.task
            state = a2a_pb2.TaskState.Name(t.status.state)
            event["task_id"] = t.id
            event["state"] = state
            if t.status.message:
                for p in t.status.message.parts:
                    if p.HasField("text"):
                        event["text"] = p.text
        elif which == "status_update":
            event["state"] = a2a_pb2.TaskState.Name(resp.status_update.state)
        events.append(event)
    return events


async def main():
    """Run the multi-agent smoke test.  Returns 0 on pass, 1 on failure."""
    # -- Step 1: Fetch both Agent Cards ----------------------------------------
    print("=== Step 1: Fetch Agent Cards ===")
    async with httpx.AsyncClient() as http:
        advisor_card = await fetch_card(http, ADVISOR_URL)
        supervisor_card = await fetch_card(http, SUPERVISOR_URL)

    print(
        f"Advisor card:   name={advisor_card.name!r}  "
        f"version={advisor_card.version!r}"
    )
    print(
        f"Supervisor card: name={supervisor_card.name!r}  "
        f"version={supervisor_card.version!r}"
    )

    # -- Step 2: Assert distinct identities ------------------------------------
    print("\n=== Step 2: Identity assertions ===")

    # 2a -- names are distinct
    assert (
        advisor_card.name != supervisor_card.name
    ), f"FAIL: both cards have same name {advisor_card.name!r}"
    print("PASS: names are distinct")

    # 2b -- Advisor name is 'ELIS Advisor'
    assert advisor_card.name == "ELIS Advisor", (
        f"FAIL: advisor card name is {advisor_card.name!r}, " "expected 'ELIS Advisor'"
    )
    print("PASS: Advisor name is 'ELIS Advisor'")

    # 2c -- Supervisor name is 'ELIS Supervisor'
    assert supervisor_card.name == "ELIS Supervisor", (
        f"FAIL: supervisor card name is {supervisor_card.name!r}, "
        "expected 'ELIS Supervisor'"
    )
    print("PASS: Supervisor name is 'ELIS Supervisor'")

    # 2d -- skill IDs are distinct
    advisor_skill_id = advisor_card.skills[0].id
    supervisor_skill_id = supervisor_card.skills[0].id
    assert (
        advisor_skill_id != supervisor_skill_id
    ), f"FAIL: both cards have same skill id {advisor_skill_id!r}"
    print("PASS: skill IDs are distinct")

    # 2e -- interfaces point to different ports
    advisor_iface_url = advisor_card.supported_interfaces[0].url
    supervisor_iface_url = supervisor_card.supported_interfaces[0].url
    assert (
        advisor_iface_url != supervisor_iface_url
    ), f"FAIL: both cards have same interface URL {advisor_iface_url!r}"
    assert "9500" in advisor_iface_url, (
        f"FAIL: Advisor interface URL missing port 9500: " f"{advisor_iface_url!r}"
    )
    assert "9501" in supervisor_iface_url, (
        f"FAIL: Supervisor interface URL missing port 9501: "
        f"{supervisor_iface_url!r}"
    )
    print("PASS: interface URLs are distinct and correct")

    # -- Step 3: Instantiate official SDK clients ------------------------------
    print("\n=== Step 3: Instantiate clients ===")
    factory = ClientFactory()
    advisor_client = factory.create(advisor_card)
    supervisor_client = factory.create(supervisor_card)
    print("PASS: both clients instantiated via ClientFactory")

    # -- Step 4: Send diagnostic messages --------------------------------------
    print("\n=== Step 4: Send diagnostic messages ===")

    advisor_events = await send_message_and_collect(
        advisor_client, "Gate 2C smoke-test ping for Advisor"
    )
    print(f"Advisor -- received {len(advisor_events)} event(s)")

    supervisor_events = await send_message_and_collect(
        supervisor_client, "Gate 2C smoke-test ping for Supervisor"
    )
    print(f"Supervisor -- received {len(supervisor_events)} event(s)")

    # -- Step 5: Assert both complete successfully -----------------------------
    print("\n=== Step 5: Completion assertions ===")

    def find_completion_text(events):
        """Extract the completion text from event stream, or None."""
        for e in events:
            if e["type"] == "task" and e.get("state") == "TASK_STATE_COMPLETED":
                return e.get("text")
        return None

    advisor_text = find_completion_text(advisor_events)
    supervisor_text = find_completion_text(supervisor_events)

    assert advisor_text is not None, "FAIL: Advisor did not reach TASK_STATE_COMPLETED"
    print("PASS: Advisor completed")

    assert (
        supervisor_text is not None
    ), "FAIL: Supervisor did not reach TASK_STATE_COMPLETED"
    print("PASS: Supervisor completed")

    # -- Step 6: Assert response identifies correct agent ----------------------
    print("\n=== Step 6: Agent identification in responses ===")

    assert "Advisor" in advisor_text, (
        f"FAIL: Advisor response does not identify as Advisor: " f"{advisor_text!r}"
    )
    print("PASS: Advisor response identifies Advisor")

    assert "Supervisor" in supervisor_text, (
        f"FAIL: Supervisor response does not identify as Supervisor: "
        f"{supervisor_text!r}"
    )
    print("PASS: Supervisor response identifies Supervisor")

    # -- Step 7: Assert no cross-port identity confusion -----------------------
    print("\n=== Step 7: Cross-port identity check ===")

    assert (
        "Supervisor" not in advisor_text
    ), f"FAIL: Advisor response contains 'Supervisor': {advisor_text!r}"
    print("PASS: Advisor response does not mention Supervisor")

    assert (
        "Advisor" not in supervisor_text
    ), f"FAIL: Supervisor response contains 'Advisor': {supervisor_text!r}"
    print("PASS: Supervisor response does not mention Advisor")

    # -- Result ----------------------------------------------------------------
    print("\n=== RESULT: PASS ===")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
