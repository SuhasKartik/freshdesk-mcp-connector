from pathlib import Path

import pytest

from freshdesk_connector.repositories.mock_repository import (
    MockTicketRepository,
)


DATA_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "mock_tickets.json"
)


@pytest.fixture
def repository() -> MockTicketRepository:
    return MockTicketRepository(DATA_FILE)


def test_search_tickets_returns_matching_ticket(repository):
    results = repository.search_tickets(query="payment")

    assert len(results) == 1
    assert results[0].id == 1002
    assert results[0].subject == "Payment failed"


def test_search_tickets_with_status_filter(repository):
    results = repository.search_tickets(status="Open")

    assert len(results) == 2

    assert all(
        ticket.status == "Open"
        for ticket in results
    )


def test_search_tickets_with_priority_filter(repository):
    results = repository.search_tickets(priority="Urgent")

    assert len(results) == 1
    assert results[0].id == 1003


def test_get_ticket_returns_ticket(repository):
    ticket = repository.get_ticket(1002)

    assert ticket is not None
    assert ticket.id == 1002


def test_get_ticket_returns_none_for_missing_ticket(repository):
    ticket = repository.get_ticket(9999)

    assert ticket is None


def test_invalid_limit_raises_error(repository):
    with pytest.raises(ValueError):
        repository.search_tickets(limit=0)

def test_list_tickets_returns_page(repository):
    results = repository.list_tickets(
        limit=2,
        page=1,
    )

    assert len(results) == 2
    assert results[0].id == 1001
    assert results[1].id == 1002


def test_list_tickets_returns_second_page(repository):
    results = repository.list_tickets(
        limit=2,
        page=2,
    )

    assert len(results) == 1
    assert results[0].id == 1003