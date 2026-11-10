# Specification: product-master-data-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read the project input (`product-requirements-document.md` and `intent.md` at the solution root)
- [x] Bootstrap agent code in `assets/product-master-data-agent/` using instructions from the `sap-agent-bootstrap` skill (invoke from inside `assets/product-master-data-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

> Based on the PRD, the agent performs simple read-only lookups (name, description, category) with no complex branching logic or multi-step workflows. No runtime skill is required — the system prompt is sufficient.

---

## Project-Specific Tasks

### System Prompt

- [x] Open `assets/product-master-data-agent/app/agent.py` and implement the system prompt with the following instructions:
  - The agent is a Product Master Data Assistant for Sales Representatives
  - It answers natural language questions about SAP S/4HANA product master data: product name, description, and category
  - It MUST use MCP tools to retrieve live data — never fabricate, guess, or invent product information
  - If a query is ambiguous (e.g. multiple products could match), the agent asks a clarifying question before calling the tool
  - If a product is not found, the agent clearly states "Product not found" rather than guessing
  - If a tool call fails or the API is unreachable, the agent informs the user and suggests checking SAP S/4HANA directly
  - When calling tools that support pagination, always set the page size parameter (`top`, `limit`, etc.) to a maximum of 100 items
  - The agent only answers questions about product master data (name, description, category); for questions about pricing, stock, orders, or other data it responds that these are outside its scope
  - Relay tool errors verbatim without embellishment

### Product Master Data Queries (R1, R2)

- [x] Ensure the agent can handle the following natural language query patterns:
  - "What is [product name / product ID]?" → returns product name and description
  - "What category does [product] belong to?" → returns product category
  - "Tell me about product [X]" → returns name, description, and category
  - "What does [product] do?" → returns product description
- [x] Ensure the agent performs a single MCP tool call per query to the Product Master API — one call that retrieves all needed fields (name, description, category)
- [x] Ensure the agent formats its response in clear, readable natural language (not raw JSON or technical field names)

### Graceful Error Handling (R5)

- [x] Ensure the agent handles the following failure scenarios:
  - Product not found → clear message: "I could not find a product matching [X]. Please check the product name or ID and try again."
  - API unreachable / tool error → clear message: "I was unable to retrieve product data at this time. Please try again or check SAP S/4HANA directly."
  - Query outside scope → clear message: "I can only answer questions about product name, description, and category. For [pricing / stock / other], please use SAP S/4HANA directly."
  - Ambiguous query → clarifying question: "I found multiple products matching [X]. Could you provide more detail or the product ID?"

---

## Data Dependencies

_No Data Product ORD IDs. API integration via MCP translation file (Path A)._

---

## API Integration

MCP API: `sap.s4:apiResource:API_PRODUCT_SRV:v1`
MCP tool scope: read-only
Resources in scope: Product, ProductDescription, ProductBasicText

- [x] API spec file already downloaded to `specification/product-master-data-agent/api-specs/API_PRODUCT_SRV.edmx`
- [x] Invoke the `mcp-translation-file` skill to generate the MCP translation file from `specification/product-master-data-agent/api-specs/API_PRODUCT_SRV.edmx`
  - MCP tool scope: read-only
  - Resources in scope: `Product`, `ProductDescription`, `ProductBasicText`
- [x] Invoke the `setup-solution` skill to create and register the MCP server asset for the generated translation file
- [x] Read the generated MCP server `asset.yaml` and copy the exact `ordId` value (do NOT invent or guess)
- [x] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from the `mcp_tools` module (canonical pattern from `guidelines-agent-python.md`) — NEVER import directly from `sap_cloud_sdk.agentgateway`, NEVER create direct HTTP clients
- [x] Add the MCP server dependency to `assets/product-master-data-agent/asset.yaml` under `requires` using the exact ORD ID from the generated `asset.yaml`
- [x] Generate `mcp-mock.json` using the `mcp-mock-config` skill (required before tests can run)

---

## Business Instrumentation

- [x] Implement business step instrumentation for all four milestones from the PRD using structured logging and OpenTelemetry spans:

  **M1 — API Connection:**
  - Log on achievement: `M1.achieved: Product Master API connection established; live data retrieved successfully`
  - Log on miss: `M1.missed: Product Master API connection failed; MCP tool or API configuration requires review`

  **M2 — Natural Language Query:**
  - Log on achievement: `M2.achieved: Natural language query interpreted and product data returned successfully`
  - Log on miss: `M2.missed: Natural language query could not be resolved; intent classification or tool call failed`

  **M3 — Joule Integration:**
  - Log on achievement: `M3.achieved: Agent accessible via SAP Joule; A2A registration confirmed`
  - Log on miss: `M3.missed: Joule integration not completed; A2A protocol registration or Joule configuration requires review`

  **M4 — Validation:**
  - Log on achievement: `M4.achieved: Validation complete; agent approved for go-live`
  - Log on miss: `M4.missed: Validation failed; outstanding issues must be resolved before go-live`

- [x] Use the decorator form (`@tracer.start_as_current_span("name")`) on regular async methods; extract business logic from `stream()` into a plain async helper (e.g. `_run_agent()`) to avoid `GeneratorExit` context errors — see `guidelines-agent-python.md`
- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns. This asset uses **Path A** (API spec files, no existing MCP server).

- [x] Verify `specification/product-master-data-agent/api-specs/API_PRODUCT_SRV.edmx` exists (already downloaded)
- [x] After `mcp-translation-file` and `setup-solution` complete, confirm these files exist:
  - `specification/product-master-data-agent/mcps/API_PRODUCT_SRV/api-spec.edmx`
  - `specification/product-master-data-agent/mcps/API_PRODUCT_SRV/translation.json`
  - `specification/product-master-data-agent/mcps/API_PRODUCT_SRV/.tool-list.json`
- [x] Add MCP server to `assets/product-master-data-agent/asset.yaml` under `requires`:
  ```yaml
  requires:
    - name: product-master-mcp-server
      kind: mcp-server
      ordId: customer.build:apiResource:product-master-data-1782e.sap-s4-product-srv-mcp-server:v1
  ```

---

## Testing

> See [guidelines-agent-python.md](../guidelines-agent-python.md) for Python testing setup and patterns.

- [x] `conftest.py` only sets `IBD_TESTING=true` — this causes the agent to use mock MCP tool results during tests
- [x] Write unit tests in `assets/product-master-data-agent/tests/` — exactly one per MCP tool used; run each immediately after writing. Test scenarios:
  - Successful product query returning name, description, category
  - Product not found — agent returns clear "not found" message
  - API error — agent returns graceful error message
  - Ambiguous query — agent asks a clarifying question
  - Out-of-scope query (e.g. pricing) — agent returns out-of-scope message
- [x] Write one integration test executing end-to-end agent flow: simulated Sales Rep query → MCP tool call (mocked) → natural language response (LLM mocked)
- [x] Run `pytest` from `assets/product-master-data-agent/` (no args) — if coverage < 70%, add tests until threshold met
- [x] Run `pytest` again from `assets/product-master-data-agent/` (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/product-master-data-agent/`

---

## Validation Checklist

```bash
# Instrumentation
grep -r "M[0-9]\.achieved" assets/product-master-data-agent/app/     # must return results

# Test report
ls assets/product-master-data-agent/test_report.json                  # must exist
```
