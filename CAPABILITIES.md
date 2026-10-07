# Freshdesk MCP Connector — Agent Capabilities

## Overview

The Freshdesk MCP Connector provides an AI agent with controlled, read-only access to Freshdesk ticket information.

The connector intentionally exposes only the operations required for ticket retrieval and search.

It does not provide write or administrative capabilities.

---

# 1. What the Agent Can Do

## 1.1 Check Connector Health

The agent can call:

```text
health_check()
```

This verifies that the MCP connector is running.

---

## 1.2 List Tickets

The agent can retrieve a paginated list of Freshdesk tickets using:

```text
list_tickets(limit, page)
```

Example:

```text
list_tickets(limit=10, page=1)
```

The agent can use this to inspect ticket information such as:

- Ticket ID
- Subject
- Description
- Status
- Priority
- Requester

---

## 1.3 Search Tickets

The agent can search Freshdesk tickets using:

```text
search_tickets(query, status, priority, limit)
```

The live Freshdesk implementation uses Freshdesk search expressions.

Examples:

```text
priority:4
```

```text
status:3
```

```text
type:'Question'
```

The agent can also combine supported filters.

For example:

```text
query="type:'Question'"
status="Pending"
priority="Urgent"
```

The connector converts supported status and priority names into Freshdesk's corresponding numeric identifiers.

---

## 1.4 Retrieve an Individual Ticket

The agent can retrieve a specific ticket using:

```text
get_ticket(ticket_id)
```

Example:

```text
get_ticket(ticket_id=1001)
```

If the ticket does not exist, the connector returns a structured not-found response rather than exposing an unhandled exception.

---

# 2. What Information the Agent Can Read

The normalized ticket model contains:

```text
id
subject
description
status
priority
requester
```

The connector converts Freshdesk-specific API fields into this normalized structure before returning the result to the agent.

This prevents the agent-facing interface from being tightly coupled to Freshdesk's raw API response format.

---

# 3. What the Agent Cannot Do

The connector is intentionally read-only.

The agent cannot:

- Create tickets
- Update tickets
- Delete tickets
- Reply to customers
- Add ticket notes
- Change ticket status
- Change ticket priority
- Modify ticket fields
- Modify customer records
- Modify contacts
- Create or delete contacts
- Perform Freshdesk administrative operations

No MCP tools for these operations are exposed.

---

# 4. Why the Connector Is Read-Only

The assignment requires the agent to read merchant data.

Adding write capabilities would increase the potential impact of an incorrect AI-generated action.

For example, if an AI agent incorrectly decided to close a ticket, a write-enabled connector could modify production customer data.

By keeping the connector read-only, the potential blast radius is significantly reduced.

If write operations were added in the future, they should be protected with additional:

- Authorization
- Input validation
- Audit logging
- Permission checks
- Monitoring
- Potential human approval

---

# 5. Authentication

Live Freshdesk access requires:

```text
FRESHDESK_DOMAIN
FRESHDESK_API_KEY
```

These values are loaded from environment variables.

Credentials are not hard-coded in the application.

The project does not include real API keys or passwords.

---

# 6. Mock Mode

The connector supports a mock mode for development and testing.

Configuration:

```env
FRESHDESK_MODE=mock
```

Mock mode uses:

```text
data/mock_tickets.json
```

The mock dataset contains synthetic ticket information.

This allows the MCP server and its tools to be tested without:

- A real Freshdesk account
- A real API key
- Network access
- Production customer data

---

# 7. Live Mode

The connector can be configured to use a real Freshdesk account:

```env
FRESHDESK_MODE=live
FRESHDESK_DOMAIN=your-domain.freshdesk.com
FRESHDESK_API_KEY=your-api-key
```

In live mode, the request flow is:

```text
AI Agent
   |
   v
MCP Tool
   |
   v
Freshdesk Repository
   |
   v
Freshdesk HTTP Client
   |
   v
Freshdesk REST API
```

The API key is used only by the HTTP client when communicating with Freshdesk.

---

# 8. Rate-Limit Protection

The connector handles HTTP `429 Too Many Requests` responses.

When Freshdesk rate-limits a request, the connector:

1. Detects the 429 response.
2. Checks for a `Retry-After` value.
3. Waits for the specified duration when available.
4. Uses exponential backoff when it is not available.
5. Retries up to a configured maximum.
6. Returns an error if the request continues to fail.

This prevents immediate failures during temporary API rate limiting while avoiding unlimited retries.

---

# 9. Input Validation

The connector validates tool inputs before performing operations.

Examples include:

- Ticket ID must be positive.
- Page number must be at least 1.
- List/search limits must remain within supported bounds.
- Unsupported status values are rejected.
- Unsupported priority values are rejected.

This reduces invalid requests reaching the Freshdesk API.

---

# 10. Error Handling

The connector handles common failures including:

### Invalid input

Returns a structured validation error.

### Ticket not found

A Freshdesk 404 is converted into a not-found result.

### API errors

Freshdesk HTTP errors are converted into `FreshdeskAPIError`.

### Rate limiting

HTTP 429 responses are retried using the retry strategy.

### Missing mock data

The connector reports a file-not-found error instead of silently returning incorrect data.

---

# 11. Capability Boundary

The connector follows a least-privilege approach.

```text
                  Freshdesk
                     |
             +-------+-------+
             |               |
          READ            WRITE
             |               |
             v               X
       MCP Connector
             |
             v
           Agent
```

The agent receives only the read capabilities required by the assignment.

---

# 12. MCP Tool Summary

| Tool | Allowed | Purpose |
|---|---|---|
| `health_check` | Yes | Check connector availability |
| `list_tickets` | Yes | List tickets |
| `search_tickets` | Yes | Search/filter tickets |
| `get_ticket` | Yes | Retrieve one ticket |
| Create ticket | No | Not exposed |
| Update ticket | No | Not exposed |
| Delete ticket | No | Not exposed |
| Reply to ticket | No | Not exposed |
| Modify customer | No | Not exposed |
| Administrative operations | No | Not exposed |

---

# 13. Data Safety

The project intentionally avoids including real merchant data.

The repository contains:

- Synthetic mock ticket data
- No production customer records
- No real passwords
- No real API keys
- No authentication tokens

The `.env` file is excluded from version control.

Only `.env.example` should be committed.

---

# 14. Current Limitations

The connector currently has the following limitations:

1. Only Freshdesk ticket operations are implemented.
2. Orders and inventory are outside the scope of this connector.
3. The connector is read-only.
4. Authentication currently uses an API key rather than OAuth.
5. Live behavior depends on Freshdesk availability and account permissions.
6. Search queries in live mode must follow Freshdesk search-expression syntax.
7. Mock mode is intended for development and testing and does not reproduce every behavior of a production Freshdesk account.
8. The connector does not expose Freshdesk administrative functionality.

---

# 15. Future Extensions

Potential future capabilities include:

### Additional Freshdesk resources

- Contacts
- Companies
- Conversations
- Agents
- Groups

### Controlled write operations

If business requirements require writes, the connector could eventually expose operations such as:

```text
create_ticket()
update_ticket()
add_ticket_note()
reply_to_ticket()
```

These should not be added without appropriate authorization, validation, audit logging, and security controls.

### OAuth

OAuth could be introduced if the system requires delegated user-level authorization or multi-tenant access.

### Observability

Production deployment could add:

- Structured logs
- Request tracing
- API latency metrics
- Error metrics
- Rate-limit metrics
- Retry metrics

---

# 16. Capability Philosophy

The connector follows three principles:

### Least privilege

Expose only the capabilities the agent actually needs.

### Explicit boundaries

Clearly distinguish what the agent can read from what it cannot modify.

### Safe failure

Invalid requests, API failures and rate limits should produce controlled responses rather than unexpected behavior.

---

# 17. Summary

The Freshdesk MCP Connector gives an AI agent controlled access to Freshdesk ticket information.

### The agent CAN:

- Check connector health
- List tickets
- Search tickets
- Filter tickets
- Retrieve individual tickets
- Read normalized ticket information

### The agent CANNOT:

- Create tickets
- Modify tickets
- Delete tickets
- Reply to customers
- Modify customer records
- Perform administrative operations

The connector therefore provides a deliberately limited, read-only integration boundary between an AI agent and Freshdesk.