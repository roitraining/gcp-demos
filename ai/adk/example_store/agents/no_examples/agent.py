from google.adk.agents import LlmAgent

from orders import INSTRUCTION, MODEL, get_order_status, log_examples

root_agent = LlmAgent(
    name="order_support",
    model=MODEL,
    instruction=INSTRUCTION,
    tools=[get_order_status],
    before_model_callback=log_examples,
)
