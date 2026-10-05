"""The few-shot examples the store holds: two per intent.

Each example is a user message, the steps the model should take, and a
search_key. The store embeds the search_key, so it is what a query matches.
"""


def _text(role, text):
  return {"content": {"role": role, "parts": [{"text": text}]}}


def _example(user, *steps):
  return {
      "search_key": user,
      "contents_example": {
          "contents": [{"role": "user", "parts": [{"text": user}]}],
          "expected_contents": list(steps),
      },
  }


def _lookup(order_id, status, eta):
  """A get_order_status call and its response."""
  return [
      {"content": {"role": "model", "parts": [{"function_call": {
          "name": "get_order_status", "args": {"order_id": order_id}}}]}},
      {"content": {"role": "user", "parts": [{"function_response": {
          "name": "get_order_status",
          "response": {"order_id": order_id, "status": status, "eta": eta}}}]}},
  ]


EXAMPLES = [
    # Order status: look it up, then answer in one fixed line.
    _example(
        "Where is order 2210?",
        *_lookup("2210", "shipped", "Monday"),
        _text("model", "Order 2210: shipped, arrives Monday."),
    ),
    _example(
        "Has my order 1875 shipped yet?",
        *_lookup("1875", "processing", "Thursday"),
        _text("model", "Order 1875: processing, arrives Thursday."),
    ),
    # Missing order ID: ask for it; don't guess or call the tool.
    _example(
        "Where's my package?",
        _text("model", "Which order? Send me the four-digit order number."),
    ),
    _example(
        "My order hasn't arrived and I'm getting worried.",
        _text("model", "Which order? Send me the four-digit order number."),
    ),
    # Refund: one fixed policy sentence, no tool call.
    _example(
        "I want a refund for order 6032.",
        _text("model", "Refunds are handled by our returns team at"
              " returns.example.com within 30 days of delivery."),
    ),
    _example(
        "Can I get my money back? The item arrived broken.",
        _text("model", "Refunds are handled by our returns team at"
              " returns.example.com within 30 days of delivery."),
    ),
    # Off-topic: one sentence back to orders.
    _example(
        "What's the weather like today?",
        _text("model", "I can only help with orders. Do you have an order"
              " number?"),
    ),
    _example(
        "Can you recommend a good laptop?",
        _text("model", "I can only help with orders. Do you have an order"
              " number?"),
    ),
]
