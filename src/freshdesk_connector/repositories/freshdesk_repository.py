from typing import Any

from freshdesk_connector.clients.freshdesk_client import FreshdeskClient
from freshdesk_connector.models import Ticket


STATUS_NAMES = {
    2: "Open",
    3: "Pending",
    4: "Resolved",
    5: "Closed",
}

PRIORITY_NAMES = {
    1: "Low",
    2: "Medium",
    3: "High",
    4: "Urgent",
}


class FreshdeskTicketRepository:
    """Ticket repository backed by the Freshdesk REST API."""

    def __init__(self, client: FreshdeskClient):
        self.client = client

    def list_tickets(
        self,
        limit: int = 10,
        page: int = 1,
    ) -> list[Ticket]:
        """Return a page of tickets from Freshdesk."""

        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100.")

        if page < 1:
            raise ValueError("Page must be greater than or equal to 1.")

        response = self.client.get(
            "/tickets",
            params={
                "page": page,
                "per_page": limit,
            },
        )

        if not isinstance(response, list):
            raise ValueError(
                "Unexpected Freshdesk ticket list response."
            )

        return [
            self._normalize_ticket(ticket)
            for ticket in response
        ]

    def search_tickets(
    self,
    query: str = "",
    status: str = "",
    priority: str = "",
    limit: int = 10,
    ) -> list[Ticket]:
        """
        Search Freshdesk tickets.

        The query is treated as a Freshdesk search expression.
        Examples:
            priority:4
            status:2
            type:'Question'
            tag:'billing'
        """

        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100.")

        search_expression = self._build_search_query(
            query=query,
            status=status,
            priority=priority,
        )

        if not search_expression:
            return self.list_tickets(limit=limit)

        response = self.client.get(
            "/search/tickets",
            params={
                "query": f'"{search_expression}"',
            },
        )

        if not isinstance(response, dict):
            raise ValueError(
                "Unexpected Freshdesk search response."
            )

        results = response.get("results", [])

        if not isinstance(results, list):
            raise ValueError(
                "Unexpected Freshdesk search results."
            )

        return [
            self._normalize_ticket(ticket)
            for ticket in results[:limit]
        ]

    def get_ticket(self, ticket_id: int) -> Ticket | None:
        """Retrieve a Freshdesk ticket by ID."""

        if ticket_id <= 0:
            raise ValueError("Ticket ID must be positive.")

        try:
            response = self.client.get(
                f"/tickets/{ticket_id}"
            )
        except Exception as exc:
            if getattr(exc, "status_code", None) == 404:
                return None
            raise

        if not isinstance(response, dict):
            raise ValueError(
                "Unexpected Freshdesk ticket response."
            )

        return self._normalize_ticket(response)

    @staticmethod
    def _build_search_query(
        query: str,
        status: str = "",
        priority: str = "",
    ) -> str:
        """Build a Freshdesk search expression."""

        parts: list[str] = []

        query = query.strip()

        if query:
            parts.append(query)

        if status:
            status_id = FreshdeskTicketRepository._status_to_id(
                status
            )

            if status_id is None:
                raise ValueError(
                    f"Unsupported ticket status: {status}"
                )

            parts.append(f"status:{status_id}")

        if priority:
            priority_id = FreshdeskTicketRepository._priority_to_id(
                priority
            )

            if priority_id is None:
                raise ValueError(
                    f"Unsupported ticket priority: {priority}"
                )

            parts.append(f"priority:{priority_id}")

        return " AND ".join(parts)

    @staticmethod
    def _status_to_id(status: str) -> int | None:
        """Convert a status name to its Freshdesk ID."""

        normalized = status.strip().lower()

        for status_id, name in STATUS_NAMES.items():
            if name.lower() == normalized:
                return status_id

        return None

    @staticmethod
    def _priority_to_id(priority: str) -> int | None:
        """Convert a priority name to its Freshdesk ID."""

        normalized = priority.strip().lower()

        for priority_id, name in PRIORITY_NAMES.items():
            if name.lower() == normalized:
                return priority_id

        return None

    @staticmethod
    def _normalize_ticket(data: dict[str, Any]) -> Ticket:
        """Convert a Freshdesk ticket into our normalized model."""

        requester = data.get("requester")

        if isinstance(requester, dict):
            requester_value = (
                requester.get("email")
                or requester.get("name")
                or str(data.get("requester_id", ""))
            )
        elif requester:
            requester_value = str(requester)
        else:
            requester_value = str(
                data.get("requester_email")
                or data.get("requester_id")
                or ""
            )

        return Ticket(
            id=int(data["id"]),
            subject=str(data.get("subject", "")),
            description=str(data.get("description_text") or ""),
            status=STATUS_NAMES.get(
                int(data.get("status", 0)),
                str(data.get("status", "")),
            ),
            priority=PRIORITY_NAMES.get(
                int(data.get("priority", 0)),
                str(data.get("priority", "")),
            ),
            requester=requester_value,
        )