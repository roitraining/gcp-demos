"""The order tool, instruction, and model shared by both agents."""

import re

MODEL = "gemini-3.7-flash"

INSTRUCTION = (
    "You are the order-support agent for an online store. Use"
    " get_order_status to look up an order."
)

_ORDERS = {
    "4417": {"status": "shipped", "eta": "Tuesday"},
    "3318": {"status": "processing", "eta": "Friday"},
    "5521": {"status": "delivered", "eta": None},
}


def get_order_status(order_id: str) -> dict:
  """Looks up the status of an order by its four-digit order ID."""
  order = _ORDERS.get(order_id)
  if order is None:
    return {"order_id": order_id, "status": "not_found"}
  return {"order_id": order_id, **order}


def log_examples(callback_context, llm_request):
  """Prints the user line of each example ExampleTool added to this request."""
  instruction = llm_request.config.system_instruction or ""
  block = re.search(r"<EXAMPLES>(.*)<EXAMPLES>", str(instruction), re.S)
  if block is None:
    print("[examples] none in this request")
    return None
  queries = re.findall(r"Begin example\n\[user\]\n(.*?)\n", block.group(1))
  print(f"[examples] {len(queries)} in this request")
  for query in queries:
    print(f"[examples]   {query}")
  return None
