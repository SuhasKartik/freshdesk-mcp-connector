import httpx

from freshdesk_connector import server
from freshdesk_connector.clients.freshdesk_client import FreshdeskClient
from freshdesk_connector.repositories.freshdesk_repository import (
    FreshdeskTicketRepository,
)


def make_live_repository(handler):
    """Create a Freshdesk repository using mocked HTTP."""

    client = FreshdeskClient(
        domain="example.freshdesk.com",
        api_key="test-api-key",
        sleep_fn=lambda _: None,
    )

    # Replace the real HTTP client with a mocked transport.
    client.client.close()

    client.client = httpx.Client(
        base_url=client.base_url,
        auth=("test-api-key", "X"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        transport=httpx.MockTransport(handler),
        timeout=client.timeout,
    )

    return FreshdeskTicketRepository(client)


def test_mcp_list_tickets_uses_live_repository(monkeypatch):
    """Verify MCP list_tickets reaches the Freshdesk repository."""

    def handler(request):
        assert request.url.path == "/api/v2/tickets"
        assert request.url.params["page"] == "1"
        assert request.url.params["per_page"] == "1"

        return httpx.Response(
            200,
            json=[
                {
                    "id": 2001,
                    "subject": "Login problem",
                    "description_text": "Customer cannot log in.",
                    "status": 2,
                    "priority": 3,
                    "requester": {
                        "email": "test@example.com"
                    },
                }
            ],
        )

    repository = make_live_repository(handler)

    monkeypatch.setenv("FRESHDESK_MODE", "live")
    monkeypatch.setattr(
        server,
        "ticket_repository",
        repository,
    )

    result = server.list_tickets(
        limit=1,
        page=1,
    )

    assert result["source"] == "live"
    assert result["total"] == 1
    assert result["tickets"][0]["id"] == 2001
    assert result["tickets"][0]["subject"] == "Login problem"
    assert result["tickets"][0]["status"] == "Open"
    assert result["tickets"][0]["priority"] == "High"

    repository.client.close()


def test_mcp_search_tickets_uses_live_repository(monkeypatch):
    """Verify MCP search_tickets reaches the Freshdesk search API."""

    def handler(request):
        assert request.url.path == "/api/v2/search/tickets"

        search_query = request.url.params["query"]

        assert "type:'Question'" in search_query
        assert "status:3" in search_query
        assert "priority:4" in search_query

        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": 2002,
                        "subject": "Payment issue",
                        "description_text": "Payment failed.",
                        "status": 3,
                        "priority": 4,
                        "requester": {
                            "email": "customer@example.com"
                        },
                    }
                ]
            },
        )

    repository = make_live_repository(handler)

    monkeypatch.setenv("FRESHDESK_MODE", "live")
    monkeypatch.setattr(
        server,
        "ticket_repository",
        repository,
    )

    result = server.search_tickets(
        query="type:'Question'",
        status="Pending",
        priority="Urgent",
        limit=5,
    )

    assert result["source"] == "live"
    assert result["total"] == 1
    assert result["tickets"][0]["id"] == 2002
    assert result["tickets"][0]["status"] == "Pending"
    assert result["tickets"][0]["priority"] == "Urgent"

    repository.client.close()


def test_mcp_get_ticket_uses_live_repository(monkeypatch):
    """Verify MCP get_ticket reaches the Freshdesk ticket API."""

    def handler(request):
        assert request.url.path == "/api/v2/tickets/2003"

        return httpx.Response(
            200,
            json={
                "id": 2003,
                "subject": "Application crash",
                "description_text": "The application crashes on startup.",
                "status": 2,
                "priority": 4,
                "requester": {
                    "email": "customer@example.com"
                },
            },
        )

    repository = make_live_repository(handler)

    monkeypatch.setenv("FRESHDESK_MODE", "live")
    monkeypatch.setattr(
        server,
        "ticket_repository",
        repository,
    )

    result = server.get_ticket(2003)

    assert result["source"] == "live"
    assert result["ticket"]["id"] == 2003
    assert result["ticket"]["subject"] == "Application crash"
    assert result["ticket"]["status"] == "Open"
    assert result["ticket"]["priority"] == "Urgent"

    repository.client.close()