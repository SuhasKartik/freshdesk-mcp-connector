# Freshdesk MCP Connector

A private Model Context Protocol (MCP) connector that enables an AI agent to securely read Freshdesk support tickets through a controlled set of MCP tools.

The connector provides ticket listing, searching, and retrieval capabilities while keeping Freshdesk-specific API logic separated from the MCP layer.

---

## 1. Project Overview

This project was built as a private merchant-tool connector using **Freshdesk**.

The goal is to provide an AI agent with controlled access to Freshdesk ticket data through MCP without exposing the agent directly to the Freshdesk REST API.

The connector supports two modes:

- **Mock mode** — uses synthetic local ticket data for development and testing.
- **Live mode** — connects to a real Freshdesk account using API-key authentication.

The connector is intentionally **read-only**. It does not create, update, delete, or reply to tickets.

---

## 2. Key Features

- MCP-based Freshdesk integration
- Read-only ticket access
- List tickets with pagination
- Search tickets using Freshdesk search expressions
- Retrieve individual tickets by ID
- Freshdesk API-key authentication
- Environment-based configuration
- HTTP error handling
- HTTP 429 rate-limit handling
- `Retry-After` support
- Exponential backoff
- Input validation
- Repository abstraction
- Mock repository for local development
- Automated unit tests
- MCP-to-HTTP integration tests
- MCP Inspector verification
- No real customer data included
- No API keys or credentials committed to the repository

---

## 3. Architecture

```text
                    AI Agent / Agent Studio
                              |
                              | MCP
                              v
                    +-------------------+
                    |     server.py     |
                    |   MCP Tool Layer  |
                    +-------------------+
                              |
                              v
                    +-------------------+
                    | TicketRepository  |
                    |     Protocol      |
                    +-------------------+
                       /             \
                      /               \
                     v                 v
          +------------------+   +-------------------------+
          | Mock Repository  |   | Freshdesk Repository    |
          +------------------+   +-------------------------+
                  |                         |
                  v                         v
        mock_tickets.json          Freshdesk Client
                                            |
                                            v
                                  Freshdesk REST API
```

### Layer responsibilities

#### MCP Server

`server.py`

Responsible for:

- Exposing MCP tools
- Validating tool inputs
- Delegating operations to the repository
- Returning agent-readable responses

#### Repository Layer

Responsible for:

- Defining ticket operations
- Abstracting the data source
- Normalizing Freshdesk responses
- Keeping provider-specific logic outside the MCP layer

Two implementations are provided:

- `MockTicketRepository`
- `FreshdeskTicketRepository`

#### HTTP Client

`freshdesk_client.py`

Responsible for:

- Freshdesk API communication
- Authentication
- HTTP requests
- API error handling
- Rate-limit handling
- Retry and backoff behavior

#### Data Models

`models.py`

Defines the normalized ticket representation using Pydantic.

---

## 4. Project Structure

```text
freshdesk_mcp_connector/
│
├── data/
│   └── mock_tickets.json
│
├── src/
│   └── freshdesk_connector/
│       ├── __init__.py
│       ├── server.py
│       ├── models.py
│       │
│       ├── clients/
│       │   ├── __init__.py
│       │   └── freshdesk_client.py
│       │
│       ├── repositories/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── mock_repository.py
│       │   └── freshdesk_repository.py
│       │
│       └── tools/
│           └── __init__.py
│
├── tests/
│   ├── test_mock_repository.py
│   ├── test_freshdesk_client.py
│   ├── test_freshdesk_repository.py
│   └── test_mcp_live_integration.py
│
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

> `.env` is local configuration and must not be committed to version control.

---

# 5. MCP Tools

The connector exposes four MCP tools.

## `health_check`

Checks whether the MCP server is running.

### Parameters

None.

### Example

```text
health_check()
```

### Response

```json
{
  "result": "Freshdesk MCP Connector is running."
}
```

---

## `list_tickets`

Returns a paginated list of Freshdesk tickets.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `limit` | integer | `10` | Maximum number of tickets to return |
| `page` | integer | `1` | Page number starting from 1 |

### Example

```text
list_tickets(limit=10, page=1)
```

### Example response

```json
{
  "total": 2,
  "tickets": [
    {
      "id": 1001,
      "subject": "Unable to log in",
      "description": "I cannot access my account.",
      "status": "Open",
      "priority": "High",
      "requester": "alex@example.com"
    }
  ],
  "source": "mock",
  "page": 1,
  "limit": 10
}
```

---

## `search_tickets`

Searches Freshdesk tickets using Freshdesk search expressions.

### Parameters

| Parameter | Type | Default | Description |
|---|---|---:|---|
| `query` | string | `""` | Freshdesk search expression |
| `status` | string | `""` | Optional ticket status |
| `priority` | string | `""` | Optional ticket priority |
| `limit` | integer | `10` | Maximum number of results |

### Examples

Search for urgent tickets:

```text
query="priority:4"
```

Search for pending tickets:

```text
query="status:3"
```

Search using a ticket type:

```text
query="type:'Question'"
```

Use the optional filters:

```text
query="type:'Question'"
status="Pending"
priority="Urgent"
```

The connector converts human-readable status and priority names into Freshdesk's numeric identifiers.

### Freshdesk status mapping

| Status | ID |
|---|---:|
| Open | 2 |
| Pending | 3 |
| Resolved | 4 |
| Closed | 5 |

### Freshdesk priority mapping

| Priority | ID |
|---|---:|
| Low | 1 |
| Medium | 2 |
| High | 3 |
| Urgent | 4 |

---

## `get_ticket`

Retrieves a single Freshdesk ticket using its ID.

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `ticket_id` | integer | Unique Freshdesk ticket ID |

### Example

```text
get_ticket(ticket_id=1001)
```

### Example response

```json
{
  "ticket": {
    "id": 1001,
    "subject": "Unable to log in",
    "description": "I cannot access my account.",
    "status": "Open",
    "priority": "High",
    "requester": "alex@example.com"
  },
  "source": "mock"
}
```

If the ticket does not exist:

```json
{
  "error": "Ticket not found",
  "ticket_id": 9999,
  "source": "mock"
}
```

---

# 6. Authentication

Live Freshdesk access uses **API-key authentication**.

The API key is provided through an environment variable and is never hard-coded into the source code.

Create a `.env` file:

```env
FRESHDESK_MODE=live
FRESHDESK_DOMAIN=your-domain.freshdesk.com
FRESHDESK_API_KEY=your-api-key
```

For local development, use mock mode:

```env
FRESHDESK_MODE=mock
FRESHDESK_DOMAIN=
FRESHDESK_API_KEY=
```

### Security rule

Never commit:

```text
.env
```

Only commit:

```text
.env.example
```

The example file contains placeholders:

```env
FRESHDESK_MODE=mock
FRESHDESK_DOMAIN=your-domain.freshdesk.com
FRESHDESK_API_KEY=your-api-key
```

---

# 7. Requirements

Recommended environment:

- Python 3.11+
- macOS/Linux/Windows
- Freshdesk account for live mode
- Freshdesk API key for live mode

Live Freshdesk credentials are **not required** to run the project in mock mode or execute the automated test suite.

---

# 8. Installation

## Step 1 — Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd freshdesk_mcp_connector
```

## Step 2 — Create a virtual environment

```bash
python3.11 -m venv .venv
```

## Step 3 — Activate the virtual environment

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows:

```powershell
.venv\Scripts\activate
```

## Step 4 — Install dependencies

```bash
pip install -e .
```

## Step 5 — Configure environment variables

Create `.env`:

```bash
cp .env.example .env
```

For local development, set:

```env
FRESHDESK_MODE=mock
```

---

# 9. Running the MCP Server

Start the MCP server with:

```bash
python src/freshdesk_connector/server.py
```

The MCP server uses **stdio transport**, allowing MCP-compatible clients such as MCP Inspector or an Agent Studio environment to communicate with it.

---

# 10. Testing with MCP Inspector

The connector can be tested using MCP Inspector.

Start the connector through MCP Inspector and verify that the following tools are available:

```text
health_check
list_tickets
search_tickets
get_ticket
```

The following operations were manually verified:

- Health check
- Ticket listing
- Ticket pagination
- Ticket search
- Individual ticket retrieval
- Ticket-not-found handling

---

# 11. Automated Testing

Run the complete test suite:

```bash
pytest -q
```

Current result:

```text
29 passed
```

The tests cover multiple layers of the application.

### Mock repository tests

Verify:

- Loading ticket data
- Ticket validation
- Searching
- Status filtering
- Priority filtering
- Pagination
- Invalid input handling

### Freshdesk client tests

Verify:

- Successful HTTP requests
- API errors
- HTTP 404/4xx/5xx handling
- Invalid configuration
- Rate-limit handling
- `Retry-After`
- Exponential backoff
- Maximum retry behavior

### Freshdesk repository tests

Verify:

- Ticket listing
- Ticket retrieval
- Ticket normalization
- Freshdesk search expressions
- Status mapping
- Priority mapping
- Invalid inputs

### MCP integration tests

The integration tests verify the complete path:

```text
MCP Tool
    ↓
Repository
    ↓
Freshdesk Client
    ↓
HTTP Transport
```

The HTTP layer uses `httpx.MockTransport`, so these tests do not make real network requests.

---

# 12. Rate-Limit Handling

The Freshdesk client handles HTTP `429 Too Many Requests` responses.

The retry strategy is:

```text
Freshdesk API
     |
     | HTTP 429
     v
Check Retry-After
     |
     +---- available ----> wait specified duration
     |
     +---- unavailable --> exponential backoff
                              |
                              v
                           retry
```

The client:

1. Detects HTTP 429.
2. Reads the `Retry-After` header when available.
3. Uses exponential backoff when `Retry-After` is unavailable.
4. Retries only up to the configured maximum.
5. Raises `FreshdeskAPIError` when retries are exhausted.

This prevents temporary API rate limits from immediately causing connector failures while avoiding infinite retries.

---

# 13. Error Handling

The connector handles failures at different layers.

### Invalid input

Examples:

```text
limit < 1
limit > maximum
page < 1
ticket_id <= 0
```

These result in validation errors.

### Freshdesk API errors

The HTTP client raises:

```text
FreshdeskAPIError
```

The error contains the HTTP status code when available.

### Ticket not found

A Freshdesk `404` for a ticket retrieval is converted into:

```json
{
  "error": "Ticket not found"
}
```

This prevents low-level HTTP details from leaking unnecessarily into the agent-facing interface.

---

# 14. Mock Mode

Mock mode uses synthetic ticket data stored at:

```text
data/mock_tickets.json
```

Example:

```json
[
  {
    "id": 1001,
    "subject": "Unable to log in",
    "description": "I cannot access my account.",
    "status": "Open",
    "priority": "High",
    "requester": "alex@example.com"
  }
]
```

The mock dataset contains no real customer information.

Mock mode is useful for:

- Development
- Automated testing
- MCP Inspector testing
- Demonstrations
- CI/CD environments
- Development without Freshdesk credentials

---

# 15. Live Mode

To connect to an actual Freshdesk account:

```env
FRESHDESK_MODE=live
FRESHDESK_DOMAIN=your-domain.freshdesk.com
FRESHDESK_API_KEY=your-api-key
```

The connector then uses:

```text
Freshdesk MCP Tool
        ↓
FreshdeskTicketRepository
        ↓
FreshdeskClient
        ↓
Freshdesk REST API
```

No changes to the MCP tool interface are required when switching between mock and live mode.

---

# 16. Data Model

Freshdesk responses are normalized into a common `Ticket` model.

```python
Ticket(
    id: int,
    subject: str,
    description: str,
    status: str,
    priority: str,
    requester: str
)
```

This prevents the MCP layer from depending directly on Freshdesk-specific response structures.

For example:

```text
Freshdesk status: 2
        ↓
Repository normalization
        ↓
Ticket.status = "Open"
```

and:

```text
Freshdesk priority: 4
        ↓
Repository normalization
        ↓
Ticket.priority = "Urgent"
```

---

# 17. Repository Pattern

The project defines a `TicketRepository` protocol.

Conceptually:

```text
TicketRepository
       |
       +---- MockTicketRepository
       |
       +---- FreshdeskTicketRepository
```

The MCP server depends on the repository contract rather than directly depending on Freshdesk.

This provides:

- Better testability
- Separation of concerns
- Easier maintenance
- Easier provider replacement
- Easier mocking

For example, the MCP server can execute:

```python
ticket_repository.get_ticket(ticket_id)
```

without needing to know whether the ticket came from:

```text
mock_tickets.json
```

or:

```text
Freshdesk REST API
```

---

# 18. What the Agent Can Do

The agent can:

- List Freshdesk tickets
- Paginate through ticket results
- Search tickets
- Filter by status
- Filter by priority
- Retrieve a ticket by ID
- Read ticket metadata
- Read ticket descriptions returned by the API

---

# 19. What the Agent Cannot Do

The connector intentionally does not expose write operations.

The agent cannot:

- Create tickets
- Update tickets
- Delete tickets
- Reply to customers
- Change ticket status
- Change ticket priority
- Modify customer records
- Modify contacts
- Perform Freshdesk administrative operations

This is a deliberate **least-privilege design**.

The assignment requires reading merchant data, so exposing unnecessary write capabilities would increase the potential impact of an incorrect AI action.

---

# 20. Security Considerations

The project follows several security principles.

### No hard-coded credentials

API keys are loaded from environment variables.

### `.env` is ignored

The `.gitignore` file prevents local credentials from being committed.

### No real customer data

Only synthetic ticket data is included.

### Read-only connector

No write or destructive operations are exposed.

### Limited API surface

Only the Freshdesk endpoints required for the assignment are used.

### Credential-free tests

Automated tests use fake credentials and mocked HTTP responses.

---

# 21. Assumptions

The project assumes:

1. The Freshdesk API key has permission to read tickets.
2. The Freshdesk domain is configured correctly.
3. The Freshdesk API is available.
4. Freshdesk search expressions follow Freshdesk's supported syntax.
5. The connector only needs ticket functionality for this assignment.
6. The connector is intended to be read-only.

---

# 22. Limitations

Current limitations include:

- Only Freshdesk tickets are supported.
- Orders and inventory are outside the scope of this connector.
- The connector is read-only.
- API-key authentication is used instead of OAuth.
- Live operation depends on Freshdesk availability and permissions.
- Search behavior in live mode follows Freshdesk search-expression syntax.
- Mock mode does not represent real production Freshdesk data.
- The connector does not currently expose Freshdesk administrative operations.
- The connector does not provide write operations such as ticket creation or updates.

---

# 23. Production Improvements

If this connector were moved toward production, the following improvements would be considered:

### Secret management

Use a dedicated secret manager rather than local `.env` files.

Examples:

- AWS Secrets Manager
- Google Secret Manager
- Azure Key Vault
- HashiCorp Vault

### Observability

Add:

- Structured logging
- Request IDs
- API latency metrics
- Error-rate metrics
- Retry metrics
- Rate-limit metrics

### Authorization

Add authorization controls around which users or agents can invoke particular tools.

### Resilience

Potential improvements:

- Circuit breaker
- More granular timeout configuration
- Better connection pooling
- Additional transient-error handling

### Testing

Add:

- Staging Freshdesk contract tests
- More failure-injection tests
- Load tests
- End-to-end tests in a controlled environment

### Deployment

Containerize the MCP connector and deploy it using an appropriate secure runtime.

---

# 24. Design Decisions

### Why MCP?

MCP provides a standardized interface through which an AI agent can discover and invoke external tools.

### Why a repository layer?

To separate business-level ticket operations from Freshdesk-specific implementation details.

### Why a separate HTTP client?

HTTP authentication, request handling, errors and retries are infrastructure concerns and should not be mixed with MCP tool definitions.

### Why mock mode?

It allows development and testing without requiring access to a real Freshdesk account.

### Why read-only?

The assignment only requires reading merchant data. Read-only access also reduces the risk of unintended AI-driven changes.

### Why environment variables?

Credentials should be configuration rather than source code and should not be committed to version control.

---

# 25. Project Validation

The project has been validated at multiple levels.

### Automated tests

```text
29 passed
```

### MCP Inspector

Verified:

```text
health_check
list_tickets
search_tickets
get_ticket
```

### Integration path

Verified:

```text
MCP Tool
    ↓
Repository
    ↓
Freshdesk Client
    ↓
Mock HTTP API
```

This provides confidence that the connector's major layers work together correctly.

---

# 26. Assignment Requirement Coverage

| Assignment Requirement          `Implementation`              | 
|---|---|
| Choose a merchant tool          Freshdesk                     | 
| Private connector               Freshdesk-specific MCP server |
| Agent can read merchant data    Ticket list/search/get tools  |
| Authentication                  Freshdesk API key             |
| List primitive                  `list_tickets`                |
| Get primitive                   `get_ticket`                  |
| Search primitive                `search_tickets`              |
| Rate-limit handling             HTTP 429 retry + backoff      |
| MCP tool specification          MCP tool definitions + README |
| Agent capabilities              Documented                    |
| Agent limitations               Documented                    |
| Setup instructions              Included                      |
| Run instructions                Included                      |
| Assumptions                     Included                      |
| Limitations                     Included                      |
| Credentials excluded            Yes                           |
| Real customer data excluded     Yes                           |
| Automated tests                 29 passing tests              |   

---

# 27. Quick Start

For the fastest local setup:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd freshdesk_mcp_connector

python3.11 -m venv .venv
source .venv/bin/activate

pip install -e .

cp .env.example .env
```

Set:

```env
FRESHDESK_MODE=mock
```

Run tests:

```bash
pytest -q
```

Expected:

```text
29 passed
```

Run the MCP server:

```bash
python src/freshdesk_connector/server.py
```

---

# 28. Final Summary

This project implements a private Freshdesk MCP connector that provides an AI agent with controlled, read-only access to support ticket data.

The system uses:

- MCP for the agent-facing tool interface
- A repository abstraction for data access
- A dedicated HTTP client for Freshdesk communication
- Pydantic models for normalized ticket data
- API-key authentication for live Freshdesk access
- Mock data for development and testing
- Retry and exponential backoff for rate limits
- Automated tests for unit and integration coverage
- Environment variables for credential management
- A least-privilege, read-only capability model

The architecture is designed to be testable, maintainable, secure, and extensible while satisfying the requirements of the merchant-tool connector assignment.
