import httpx
import pytest

from freshdesk_connector.clients.freshdesk_client import (
    FreshdeskClient,
)
from freshdesk_connector.repositories.freshdesk_repository import (
    FreshdeskTicketRepository,
)


def make_repository(handler):
    """Create a repository backed by a mocked HTTP transport."""

    client = FreshdeskClient(
        domain="example.freshdesk.com",
        api_key="test-api-key",
    )

    client.client.close()

    client.client = httpx.Client(
        base_url=client.base_url,
        auth=("test-api-key", "X"),
        transport=httpx.MockTransport(handler),
    )

    return FreshdeskTicketRepository(client)


def test_list_tickets_normalizes_response():
    def handler(request):
        assert request.url.path == "/api/v2/tickets"
        assert request.url.params["page"] == "1"
        assert request.url.params["per_page"] == "10"

        return httpx.Response(
            200,
            json=[
                {
                    "id": 1001,
                    "subject": "Unable to log in",
                    "description_text": "Cannot access account.",
                    "status": 2,
                    "priority": 3,
                    "requester_id": 501,
                }
            ],
        )

    repository = make_repository(handler)

    try:
        tickets = repository.list_tickets()

        assert len(tickets) == 1
        assert tickets[0].id == 1001
        assert tickets[0].status == "Open"
        assert tickets[0].priority == "High"
        assert tickets[0].requester == "501"
    finally:
        repository.client.close()


def test_get_ticket_returns_normalized_ticket():
    def handler(request):
        assert request.url.path == "/api/v2/tickets/1001"

        return httpx.Response(
            200,
            json={
                "id": 1001,
                "subject": "Payment failed",
                "description_text": "Payment was declined.",
                "status": 3,
                "priority": 4,
                "requester": {
                    "email": "customer@example.com"
                },
            },
        )

    repository = make_repository(handler)

    try:
        ticket = repository.get_ticket(1001)

        assert ticket is not None
        assert ticket.id == 1001
        assert ticket.status == "Pending"
        assert ticket.priority == "Urgent"
        assert ticket.requester == "customer@example.com"
    finally:
        repository.client.close()


def test_get_ticket_returns_none_for_404():
    def handler(request):
        return httpx.Response(
            404,
            json={"message": "Ticket not found"},
        )

    repository = make_repository(handler)

    try:
        ticket = repository.get_ticket(9999)

        assert ticket is None
    finally:
        repository.client.close()


def test_search_tickets_builds_search_query():
    def handler(request):
        assert request.url.path == "/api/v2/search/tickets"

        query = request.url.params["query"]

        assert "payment" in query
        assert "status:3" in query
        assert "priority:4" in query

        return httpx.Response(
            200,
            json={
                "total": 1,
                "results": [
                    {
                        "id": 1002,
                        "subject": "Payment failed",
                        "description_text": "Payment declined.",
                        "status": 3,
                        "priority": 4,
                        "requester_email": "customer@example.com",
                    }
                ],
            },
        )

    repository = make_repository(handler)

    try:
        tickets = repository.search_tickets(
            query="payment",
            status="Pending",
            priority="Urgent",
        )

        assert len(tickets) == 1
        assert tickets[0].id == 1002
        assert tickets[0].status == "Pending"
        assert tickets[0].priority == "Urgent"
    finally:
        repository.client.close()


def test_search_without_query_uses_list_endpoint():
    def handler(request):
        assert request.url.path == "/api/v2/tickets"

        return httpx.Response(
            200,
            json=[],
        )

    repository = make_repository(handler)

    try:
        tickets = repository.search_tickets()

        assert tickets == []
    finally:
        repository.client.close()


def test_invalid_list_limit_is_rejected():
    def handler(request):
        raise AssertionError("HTTP request should not happen.")

    repository = make_repository(handler)

    try:
        with pytest.raises(ValueError):
            repository.list_tickets(limit=0)
    finally:
        repository.client.close()


def test_invalid_ticket_id_is_rejected():
    def handler(request):
        raise AssertionError("HTTP request should not happen.")

    repository = make_repository(handler)

    try:
        with pytest.raises(ValueError):
            repository.get_ticket(0)
    finally:
        repository.client.close()