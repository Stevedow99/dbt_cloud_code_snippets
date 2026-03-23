# How to Set Up The dbt Platform MCP in Databricks (Concise)

## 0. Authenticate to your Databricks workspace

Before deploying your MCP server, authenticate to your workspace using OAuth.

Run the following in a local terminal:

```bash
databricks auth login --host https://<your-workspace-hostname>
```

## 1. Clone the dbt-mcp repository

```bash
git clone https://github.com/dbt-labs/dbt-mcp.git
cd dbt-mcp
```

## 2. Create `app.yaml`

Create `app.yaml` in the repository root:

```yaml
command:
  [
    "uv",
    "run",
    "dbt-mcp",
  ]
env:
  - name: MCP_TRANSPORT
    value: "streamable-http"
  - name: SETUPTOOLS_SCM_PRETEND_VERSION
    value: "0.0.0"
  - name: DBT_HOST
    value: "<your-dbt-host>"
  - name: DBT_HOST_PREFIX
    value: "<your-account-prefix>"
  - name: DBT_TOKEN
    valueFrom: dbt-token
  - name: DBT_PROD_ENV_ID
    value: "<your-production-environment-id>"
```

> **Important:** The `valueFrom` field references a **resource** that must be configured in the Databricks Apps UI (not in `app.yaml`). See Step 4a below. Do **not** use `{{secrets/...}}` syntax or a `resources` block in `app.yaml` — neither works.

## 3. Update Databricks CLI

```bash
brew upgrade databricks
```

## 4. Create dbt secrets in Databricks

**Option A: Via the Databricks CLI**

```bash
databricks secrets create-scope dbt-mcp
databricks secrets put-secret dbt-mcp dbt-token --string-value "<your-dbt-service-token>"
```

**Option B: Via a Databricks notebook**

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
SCOPE = "dbt-mcp"
w.secrets.create_scope(scope=SCOPE)
w.secrets.put_secret(scope=SCOPE, key="dbt-token", string_value="<your-dbt-service-token>")
```

## 5. Create the app and add the secret resource

First, create the app. The name is whatever you choose — it's not defined anywhere in the codebase. **The name must start with `mcp-`** for it to appear as a selectable custom MCP server in the Databricks AI Playground:

```bash
databricks apps create mcp-dbt-platform
```

Then add the dbt token as a secret resource in the UI (the `valueFrom: dbt-token` in `app.yaml` won't resolve without this):

1. Go to **Compute > Apps > mcp-dbt-platform**
2. Click **Edit** (top right)
3. In the **App resources** section, click **+ Add resource**
4. Select **Secret** as the resource type
5. Set the **secret scope** to `dbt-mcp` and **secret key** to `dbt-token`
6. Set the **resource key** to `dbt-token` (this must match the `valueFrom` value in `app.yaml`)
7. Click **Save**

Your configured resource should look like this:

![App secret resource configuration](doc_screenshots/app_sec_ss.png)

## 6. Deploy

```bash
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)
databricks sync . "/Users/$DATABRICKS_USERNAME/mcp-dbt-platform"
databricks apps deploy mcp-dbt-platform \
  --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/mcp-dbt-platform"
```

Check logs if needed:

```bash
databricks apps logs mcp-dbt-platform --tail-lines 100
```

## 7. Create a service principal for OAuth

1. Go to Databricks **Account Console > User management > Service principals**
2. Click **Add service principal** > select **Databricks managed** > name it `dbt-mcp-client`
3. Click into the new service principal > **Credentials & secrets** tab > **Generate secret**
4. Copy the **Client ID** and **Secret** immediately (secret is only shown once)
5. **Assign the service principal to your workspace**: In the Account Console, go to **Workspaces** > click into your workspace > **Permissions** > add `dbt-mcp-client`
6. **Grant the service principal access to the app**: In your workspace, go to **Compute > Apps > mcp-dbt-platform > Permissions** > add `dbt-mcp-client` with **Can Use**

## 8. Store OAuth credentials as secrets

**Option A: Via the Databricks CLI**

```bash
databricks secrets put-secret dbt-mcp oauth-client-id --string-value "<your-client-id>"
databricks secrets put-secret dbt-mcp oauth-client-secret --string-value "<your-oauth-secret>"
```

**Option B: Via a Databricks notebook**

```python
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
SCOPE = "dbt-mcp"
w.secrets.put_secret(scope=SCOPE, key="oauth-client-id", string_value="<your-client-id>")
w.secrets.put_secret(scope=SCOPE, key="oauth-client-secret", string_value="<your-oauth-secret>")
```

## 9. Connect from a notebook

```python
%pip install databricks-mcp typing_extensions nest_asyncio --upgrade
dbutils.library.restartPython()
```

```python
import nest_asyncio
nest_asyncio.apply()

from databricks_mcp import DatabricksMCPClient
from databricks.sdk import WorkspaceClient

mcp_server_url = "https://<your-app-url>/mcp"

workspace_client = WorkspaceClient(
    host="https://<your-workspace-url>",
    client_id=dbutils.secrets.get(scope="dbt-mcp", key="oauth-client-id"),
    client_secret=dbutils.secrets.get(scope="dbt-mcp", key="oauth-client-secret")
)

mcp_client = DatabricksMCPClient(server_url=mcp_server_url, workspace_client=workspace_client)

tools = mcp_client.list_tools()
print(f"Found {len(tools)} tools:")
for tool in tools:
    print(f"  - {tool.name}")
```

## 10. Call a tool

```python
result = mcp_client.call_tool("list_metrics", {})
print(result)
```

---

## Ways to Use the dbt Platform MCP in Databricks

The notebook approach above is useful for **testing the connection**, but the real value of the MCP server is giving AI tools access to your dbt project. Here's where you can use it:

- **AI Playground** — The quickest way to interact with the MCP. Go to **AI/ML > Playground**, select a model, click **Add tools > MCP Servers > Custom MCP Server**, and select your `mcp-dbt-platform` app. Ask natural language questions like "What are my top metrics by state?" and the LLM will call dbt tools to get the answer.

![Using the dbt MCP in Databricks AI Playground](doc_screenshots/dbt_platform_mcp_ai_platground.png)

- **AI Agents (Mosaic AI Agent Framework)** — Build an agent that connects to the MCP server as a tool source. The agent can reason about your dbt project — querying metrics, exploring lineage, checking model health — and be deployed as a serving endpoint for production use.

- **Genie Spaces** — Genie already has SQL/data integration, but adding the dbt MCP gives it access to semantic layer metrics, model metadata, and lineage context.

- **External AI Applications** — Any MCP-compatible client (Claude Desktop, Cursor, custom apps) can connect to the Databricks-hosted endpoint using the streamable-http transport and the app URL.

![Example: Querying the dbt Semantic Layer from Databricks AI Playground](doc_screenshots/pull_dbt_sl_example.png)
