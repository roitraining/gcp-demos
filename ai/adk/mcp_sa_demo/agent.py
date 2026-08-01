import google.auth
import google.auth.transport.requests
from google.adk.agents import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.apps import App
from google.adk.tools.mcp_tool import (McpToolset,
                                       StreamableHTTPConnectionParams)

BQ_MCP_SERVER_URL = "https://bigquery.googleapis.com/mcp"
SCOPES = ["https://www.googleapis.com/auth/bigquery"]


# Load ADC once; the credential object caches its token and knows when it expires.
_credentials, _project_id = google.auth.default(scopes=SCOPES)


def bigquery_auth_headers(readonly_context: ReadonlyContext) -> dict[str, str]:
    """Return ADC bearer token as MCP request headers.

    Called by ADK on each MCP (re)connection. Only hits the token endpoint
    when the cached token is missing or expired (~hourly), not on every call.
    """
    if not _credentials.valid:
        print('Refreshing ADC token...')
        _credentials.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {_credentials.token}",
        "x-goog-user-project": _project_id,  # quota / billing project
    }


bigquery_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url=BQ_MCP_SERVER_URL),
    header_provider=bigquery_auth_headers,
)

root_agent = Agent(
    name="bq_agent",
    model="gemini-flash-latest",
    instruction=(
        "You are a BigQuery assistant. Use the BigQuery MCP tools to list "
        "datasets and tables and to run read-only SQL queries when asked. "
        "Show the SQL you run and summarize the results."
    ),
    tools=[bigquery_toolset],
)

app = App(root_agent=root_agent, name="app")
