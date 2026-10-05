import os

from google.adk.agents import LlmAgent
from google.adk.examples import VertexAiExampleStore
from google.adk.tools.example_tool import ExampleTool

from orders import INSTRUCTION, MODEL, get_order_status, log_examples

store = VertexAiExampleStore(os.environ["EXAMPLE_STORE_NAME"])

root_agent = LlmAgent(
    name="order_support",
    model=MODEL,
    instruction=INSTRUCTION,
    tools=[get_order_status, ExampleTool(store)],
    before_model_callback=log_examples,
)
