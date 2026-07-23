"""
ADK callback examples - one small, self-contained scenario per callback type.

Reference: https://adk.dev/callbacks/types-of-callbacks/
Verified against google-adk 2.5.0.

    pip install google-adk
    export GOOGLE_API_KEY=...        # https://aistudio.google.com/app/apikey

    python adk_callback_examples.py              # run all six demos
    python adk_callback_examples.py before_tool  # run just one

Cheat sheet - what the return value means:

    callback              return None            return a value
    --------------------  ---------------------  ------------------------------------
    before_agent_callback run the agent          types.Content -> skip the agent
    after_agent_callback  keep agent output      types.Content -> appended to output
    before_model_callback send request to LLM    LlmResponse   -> skip the LLM call
    after_model_callback  keep LLM response      LlmResponse   -> replaces the response
    before_tool_callback  run the tool           dict          -> skip the tool
    after_tool_callback   keep tool result       dict          -> replaces the result

Parameter names are keyword-bound by the framework and must match exactly:
callback_context, llm_request, llm_response, tool, args, tool_context, tool_response.
Every callback below may also be declared `async def`.
"""

from __future__ import annotations

import asyncio
import re
import sys
from copy import deepcopy
from datetime import date
from typing import Any, Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.runners import InMemoryRunner
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

MODEL = "gemini-3.5-flash"


# ---------------------------------------------------------------------------
# Shared test harness
# ---------------------------------------------------------------------------
async def run_demo(
    agent: LlmAgent,
    prompt: str,
    *,
    state: Optional[dict[str, Any]] = None,
    label: str = "",
) -> None:
    """Creates a fresh in-memory session, sends one message, prints the result."""
    app_name = f"{agent.name}_demo"
    user_id, session_id = "demo_user", f"session_{abs(hash(label)) % 10_000}"

    runner = InMemoryRunner(agent=agent, app_name=app_name)
    await runner.session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=state or {},
    )

    print(f"\n--- {label}")
    print(f">>> user: {prompt}")
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
    ):
        if event.is_final_response() and event.content and event.content.parts:
            text = "".join(part.text or "" for part in event.content.parts).strip()
            if text:
                print(f"<<< {event.author}: {text}")
        elif event.error_message:
            print(f"!!! error: {event.error_message}")


# ===========================================================================
# 1. before_agent_callback - a usage quota gate
# ===========================================================================
# Scenario: each session gets a small number of credits. When they run out we
# want to answer instantly with a canned message and never touch the model, so
# no tokens are spent. Classic gatekeeper: cheap check, expensive work skipped.

def enforce_quota(callback_context: CallbackContext) -> Optional[types.Content]:
    credits = callback_context.state.get("credits_remaining", 0)

    if credits <= 0:
        print("   [before_agent] no credits left -> skipping the whole agent")
        return types.Content(
            role="model",
            parts=[types.Part(text="You've used all of today's credits. Resets at midnight UTC.")],
        )

    # Mutating state here records a delta that ADK persists with the invocation.
    callback_context.state["credits_remaining"] = credits - 1
    print(f"   [before_agent] {credits} -> {credits - 1} credits, proceeding")
    return None


quota_agent = LlmAgent(
    name="QuotaGatedAgent",
    model=MODEL,
    instruction="Answer in one short sentence.",
    before_agent_callback=enforce_quota,
)


async def demo_before_agent() -> None:
    await run_demo(
        quota_agent,
        "What's the tallest mountain in Japan?",
        state={"credits_remaining": 3},
        label="before_agent: credits available (agent runs)",
    )
    await run_demo(
        quota_agent,
        "What's the tallest mountain in Japan?",
        state={"credits_remaining": 0},
        label="before_agent: out of credits (agent skipped)",
    )


# ===========================================================================
# 2. after_agent_callback - append a compliance disclaimer
# ===========================================================================
# Scenario: a finance-adjacent assistant must never send an answer without a
# disclaimer. after_agent is the right hook because it fires once per agent run,
# no matter how many model calls or tool loops happened inside.
#
# Note the documented limitation: after_agent_callback *appends* content, it
# cannot rewrite what the agent already emitted. To rewrite text, use
# after_model_callback instead.

def append_disclaimer(callback_context: CallbackContext) -> Optional[types.Content]:
    callback_context.state["last_agent_run"] = date.today().isoformat()

    if callback_context.state.get("disclaimer_suppressed", False):
        print("   [after_agent] disclaimer suppressed for this session")
        return None

    print("   [after_agent] appending disclaimer")
    return types.Content(
        role="model",
        parts=[types.Part(text="\n\n_Educational information only - not financial advice._")],
    )


disclaimer_agent = LlmAgent(
    name="FinanceHelper",
    model=MODEL,
    instruction="Explain personal finance concepts in two sentences.",
    after_agent_callback=append_disclaimer,
)


async def demo_after_agent() -> None:
    await run_demo(
        disclaimer_agent,
        "What is dollar cost averaging?",
        label="after_agent: disclaimer appended",
    )
    await run_demo(
        disclaimer_agent,
        "What is dollar cost averaging?",
        state={"disclaimer_suppressed": True},
        label="after_agent: disclaimer suppressed",
    )


# ===========================================================================
# 3. before_model_callback - inject context, then guard the request
# ===========================================================================
# Scenario: a support bot. Two jobs on the way to the model:
#   (a) inject facts the prompt author can't know at build time - today's date
#       and the caller's plan tier, pulled from session state;
#   (b) refuse off-topic categories (legal advice) without paying for a call.
#
# Returning an LlmResponse short-circuits the model. The same shape is how you'd
# serve a cache hit.

_BLOCKED_TOPICS = ("sue", "lawsuit", "legal advice", "attorney")


def personalize_and_guard(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    # (a) Dynamic instructions. append_instructions handles the str/Content
    #     union for you, so you never poke at config.system_instruction directly.
    tier = callback_context.state.get("plan_tier", "free")
    llm_request.append_instructions(
        [f"Today is {date.today():%B %d, %Y}. The customer is on the {tier} plan."]
    )
    print(f"   [before_model] injected date + plan_tier={tier}")

    # (b) Guardrail on the last user turn.
    last_user_text = ""
    if llm_request.contents and llm_request.contents[-1].role == "user":
        last_user_text = "".join(
            part.text or "" for part in (llm_request.contents[-1].parts or [])
        )

    if any(topic in last_user_text.lower() for topic in _BLOCKED_TOPICS):
        print("   [before_model] blocked topic -> skipping the LLM call")
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text="I can't help with legal questions. Please contact a lawyer.")],
            )
        )

    return None


support_agent = LlmAgent(
    name="SupportBot",
    model=MODEL,
    instruction="You are a support agent for a bike rental company. Be brief.",
    before_model_callback=personalize_and_guard,
)


async def demo_before_model() -> None:
    await run_demo(
        support_agent,
        "How late can I return a bike?",
        state={"plan_tier": "pro"},
        label="before_model: instructions injected, call proceeds",
    )
    await run_demo(
        support_agent,
        "Can I sue you over the damage fee?",
        state={"plan_tier": "free"},
        label="before_model: blocked topic, LLM never called",
    )


# ===========================================================================
# 4. after_model_callback - redact PII on the way out
# ===========================================================================
# Scenario: the model may echo card-like or phone-like digit strings from its
# context back to the user. Scrub them before anything downstream sees them,
# and flag the session for review.
#
# Deep-copy the parts: mutating llm_response in place is visible to any other
# callback in the chain. Also guard on `partial` - in streaming mode this fires
# per chunk, and a regex can straddle a chunk boundary.

_DIGITS_RE = re.compile(r"\b\d(?:[ -]?\d){12,15}\b")


def redact_pii(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    if llm_response.partial:
        return None
    if not llm_response.content or not llm_response.content.parts:
        return None

    parts = [deepcopy(part) for part in llm_response.content.parts]
    hits = 0
    for part in parts:
        if part.text and _DIGITS_RE.search(part.text):
            part.text, n = _DIGITS_RE.subn("[REDACTED]", part.text)
            hits += n

    if not hits:
        return None

    print(f"   [after_model] redacted {hits} candidate number(s)")
    callback_context.state["pii_redacted"] = True
    return LlmResponse(
        content=types.Content(role="model", parts=parts),
        grounding_metadata=llm_response.grounding_metadata,
    )


redaction_agent = LlmAgent(
    name="RedactingAgent",
    model=MODEL,
    instruction="You are a test fixture. Follow the user's formatting request literally.",
    after_model_callback=redact_pii,
)


async def demo_after_model() -> None:
    await run_demo(
        redaction_agent,
        "Print exactly this line and nothing else: Card on file 4111 1111 1111 1111 expires soon.",
        label="after_model: digits redacted",
    )
    await run_demo(
        redaction_agent,
        "Say 'all clear' and nothing else.",
        label="after_model: nothing to redact, response passes through",
    )


# ===========================================================================
# 5. before_tool_callback - authorize a refund before it happens
# ===========================================================================
# Scenario: the model can call issue_refund. Policy says refunds over $100 need
# a manager. The model shouldn't be trusted to enforce that, so the callback
# does - deterministically, in code.
#
# Returning a dict skips execution and that dict becomes the tool result the
# model sees, so the model can explain the denial. You can also mutate `args`
# in place to sanitize inputs before the tool runs.

def issue_refund(order_id: str, amount_usd: float) -> dict:
    """Refunds an order. Returns the refund confirmation."""
    return {"status": "refunded", "order_id": order_id, "amount_usd": amount_usd}


def authorize_refund(
    tool: BaseTool, args: dict[str, Any], tool_context: ToolContext
) -> Optional[dict]:
    if tool.name != "issue_refund":
        return None

    amount = float(args.get("amount_usd", 0))
    role = tool_context.state.get("user_role", "agent")

    if amount > 100 and role != "manager":
        print(f"   [before_tool] ${amount:.2f} exceeds limit for role={role} -> tool skipped")
        return {
            "status": "denied",
            "reason": "Refunds over $100 require manager approval.",
            "escalation_url": "https://support.example.com/escalate",
        }

    # Sanitize in place - the tool receives this same dict.
    args["amount_usd"] = round(amount, 2)
    print(f"   [before_tool] approved ${args['amount_usd']:.2f} for role={role}")
    return None


refund_agent = LlmAgent(
    name="RefundAgent",
    model=MODEL,
    instruction=(
        "You process refunds. When asked, call issue_refund with the order id and amount. "
        "Report the outcome to the user, including any denial reason."
    ),
    tools=[issue_refund],
    before_tool_callback=authorize_refund,
)


async def demo_before_tool() -> None:
    await run_demo(
        refund_agent,
        "Refund order A-1002 for $45.",
        state={"user_role": "agent"},
        label="before_tool: under limit, refund runs",
    )
    await run_demo(
        refund_agent,
        "Refund order A-1003 for $250.",
        state={"user_role": "agent"},
        label="before_tool: over limit, refund blocked",
    )
    await run_demo(
        refund_agent,
        "Refund order A-1003 for $250.",
        state={"user_role": "manager"},
        label="before_tool: over limit but manager, refund runs",
    )


# ===========================================================================
# 6. after_tool_callback - trim a noisy tool result
# ===========================================================================
# Scenario: search_orders can return hundreds of rows. Feeding all of them back
# into the context is slow and expensive, and the model only needs a few to
# answer. Truncate the payload, tell the model it was truncated, and stash the
# full list in state so later steps can still reach it.
#
# The `temp:` prefix means the value lives for this invocation only and is never
# persisted to the session store.

_FAKE_DB = [{"order_id": f"A-{1000 + i}", "total_usd": 20 + i} for i in range(40)]


def search_orders(customer: str) -> dict:
    """Finds all orders for a customer."""
    return {"customer": customer, "orders": _FAKE_DB}


def trim_tool_result(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict,
) -> Optional[dict]:
    if tool.name != "search_orders":
        return None

    orders = tool_response.get("orders", [])
    if len(orders) <= 3:
        return None

    print(f"   [after_tool] trimming {len(orders)} orders down to 3")
    tool_context.state["temp:all_orders"] = orders
    return {
        **tool_response,
        "orders": orders[:3],
        "truncated": True,
        "total_matches": len(orders),
    }


order_agent = LlmAgent(
    name="OrderLookupAgent",
    model=MODEL,
    instruction=(
        "Look up orders with search_orders. Tell the user how many matched in total "
        "and list only the orders you were given."
    ),
    tools=[search_orders],
    after_tool_callback=trim_tool_result,
)


async def demo_after_tool() -> None:
    await run_demo(
        order_agent,
        "Show me the orders for customer 'Rivera'.",
        label="after_tool: large result truncated before reaching the model",
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
DEMOS = {
    "before_agent": demo_before_agent,
    "after_agent": demo_after_agent,
    "before_model": demo_before_model,
    "after_model": demo_after_model,
    "before_tool": demo_before_tool,
    "after_tool": demo_after_tool,
}


async def main() -> None:
    selected = sys.argv[1:] or list(DEMOS)
    for name in selected:
        if name not in DEMOS:
            print(f"unknown demo {name!r}; choose from: {', '.join(DEMOS)}")
            continue
        print(f"\n{'=' * 70}\n{name}_callback\n{'=' * 70}")
        await DEMOS[name]()


if __name__ == "__main__":
    asyncio.run(main())
