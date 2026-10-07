import json
from pathlib import Path

from freshdesk_connector.models import Ticket


class MockTicketRepository:
    """Repository for local mock Freshdesk tickets."""

    def __init__(self, data_file: Path):
        self.data_file = data_file

    def _load_tickets(self) -> list[Ticket]:
        """Load and validate tickets from the JSON data source."""

        if not self.data_file.exists():
            raise FileNotFoundError(
                f"Mock ticket data not found: {self.data_file}"
            )

        with self.data_file.open("r", encoding="utf-8") as file:
            raw_tickets = json.load(file)

        if not isinstance(raw_tickets, list):
            raise ValueError("Mock ticket data must be a JSON list.")

        return [
            Ticket.model_validate(ticket)
            for ticket in raw_tickets
        ]
    
    def list_tickets(
    self,
    limit: int = 10,
    page: int = 1,
    ) -> list[Ticket]:
        """Return a page of tickets from the mock data."""

        if not 1 <= limit <= 50:
            raise ValueError("Limit must be between 1 and 50.")

        if page < 1:
            raise ValueError(
                "Page must be greater than or equal to 1."
            )

        tickets = self._load_tickets()

        start = (page - 1) * limit
        end = start + limit

        return tickets[start:end]

    def search_tickets(
        self,
        query: str = "",
        status: str = "",
        priority: str = "",
        limit: int = 10,
    ) -> list[Ticket]:
        """Search tickets using text, status and priority filters."""

        if not 1 <= limit <= 50:
            raise ValueError("Limit must be between 1 and 50.")

        tickets = self._load_tickets()

        query = query.strip().lower()
        status = status.strip().lower()
        priority = priority.strip().lower()

        results: list[Ticket] = []

        for ticket in tickets:

            searchable_text = " ".join(
                [
                    ticket.subject,
                    ticket.description,
                    ticket.requester,
                ]
            ).lower()

            if query and query not in searchable_text:
                continue

            if status and ticket.status.lower() != status:
                continue

            if priority and ticket.priority.lower() != priority:
                continue

            results.append(ticket)

            if len(results) >= limit:
                break

        return results

    def get_ticket(self, ticket_id: int) -> Ticket | None:
        """Retrieve a ticket by ID."""

        tickets = self._load_tickets()

        for ticket in tickets:
            if ticket.id == ticket_id:
                return ticket

        return None