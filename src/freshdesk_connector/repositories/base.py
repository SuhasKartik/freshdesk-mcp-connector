from typing import Protocol

from freshdesk_connector.models import Ticket


class TicketRepository(Protocol):
    """Contract for ticket data providers."""

    def list_tickets(
        self,
        limit: int = 10,
        page: int = 1,
    ) -> list[Ticket]:
        """Return a page of tickets."""
        ...

    def search_tickets(
        self,
        query: str = "",
        status: str = "",
        priority: str = "",
        limit: int = 10,
    ) -> list[Ticket]:
        """Search tickets using optional filters."""
        ...

    def get_ticket(self, ticket_id: int) -> Ticket | None:
        """Retrieve a ticket by ID."""
        ...