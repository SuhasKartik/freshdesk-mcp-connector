import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from freshdesk_connector.clients.freshdesk_client import (
    FreshdeskAPIError,
    FreshdeskClient,
)
from freshdesk_connector.repositories.freshdesk_repository import (
    FreshdeskTicketRepository,
)
from freshdesk_connector.repositories.mock_repository import (
    MockTicketRepository,
)


# Load environment variables from .env
load_dotenv()


# Create the MCP server
mcp = FastMCP("Freshdesk Connector")


# Resolve the project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]


# Location of development mock data
DATA_FILE = PROJECT_ROOT / "data" / "mock_tickets.json"


def create_ticket_repository():
    """
    Create the appropriate ticket repository.

    Supported modes:

    mock:
        Uses local mock ticket data.

    live:
        Uses the real Freshdesk API with API-key authentication.
    """

    mode = os.getenv(
        "FRESHDESK_MODE",
        "mock",
    ).strip().lower()

    if mode == "mock":
        return MockTicketRepository(DATA_FILE)

    if mode == "live":
        domain = os.getenv(
            "FRESHDESK_DOMAIN",
            "",
        ).strip()

        api_key = os.getenv(
            "FRESHDESK_API_KEY",
            "",
        ).strip()

        client = FreshdeskClient(
            domain=domain,
            api_key=api_key,
        )

        return FreshdeskTicketRepository(client)

    raise ValueError(
        "Invalid FRESHDESK_MODE. "
        "Expected 'mock' or 'live'."
    )


# Create the repository once when the server starts.
ticket_repository = create_ticket_repository()


def get_source() -> str:
    """Return the currently configured data source."""

    return os.getenv(
        "FRESHDESK_MODE",
        "mock",
    ).strip().lower()


@mcp.tool()
def health_check() -> str:
    """Check whether the Freshdesk MCP server is running."""

    return "Freshdesk MCP Connector is running."


@mcp.tool()
def list_tickets(
    limit: int = 10,
    page: int = 1,
) -> dict:
    """
    List Freshdesk tickets.

    Args:
        limit: Maximum number of tickets to return.
        page: Page number starting from 1.
    """

    try:
        tickets = ticket_repository.list_tickets(
            limit=limit,
            page=page,
        )

        return {
            "total": len(tickets),
            "tickets": [
                ticket.model_dump()
                for ticket in tickets
            ],
            "source": get_source(),
            "page": page,
            "limit": limit,
        }

    except ValueError as error:
        return {
            "error": str(error),
            "source": get_source(),
        }

    except FreshdeskAPIError as error:
        return {
            "error": str(error),
            "status_code": error.status_code,
            "source": get_source(),
        }

    except FileNotFoundError as error:
        return {
            "error": str(error),
            "source": get_source(),
        }


@mcp.tool()
def search_tickets(
    query: str = "",
    status: str = "",
    priority: str = "",
    limit: int = 10,
) -> dict:
    """
    Search Freshdesk tickets.

    Args:
        query: Freshdesk search expression, such as
               'priority:4' or "type:'Question'".
        status: Optional ticket status filter.
        priority: Optional ticket priority filter.
        limit: Maximum number of tickets to return.
    """

    try:
        tickets = ticket_repository.search_tickets(
            query=query,
            status=status,
            priority=priority,
            limit=limit,
        )

        return {
            "total": len(tickets),
            "tickets": [
                ticket.model_dump()
                for ticket in tickets
            ],
            "source": get_source(),
        }

    except ValueError as error:
        return {
            "error": str(error),
            "source": get_source(),
        }

    except FreshdeskAPIError as error:
        return {
            "error": str(error),
            "status_code": error.status_code,
            "source": get_source(),
        }

    except FileNotFoundError as error:
        return {
            "error": str(error),
            "source": get_source(),
        }


@mcp.tool()
def get_ticket(ticket_id: int) -> dict:
    """
    Retrieve a Freshdesk ticket by its ID.

    Args:
        ticket_id: Unique ticket identifier.
    """

    try:
        ticket = ticket_repository.get_ticket(
            ticket_id
        )

        if ticket is None:
            return {
                "error": "Ticket not found",
                "ticket_id": ticket_id,
                "source": get_source(),
            }

        return {
            "ticket": ticket.model_dump(),
            "source": get_source(),
        }

    except ValueError as error:
        return {
            "error": str(error),
            "source": get_source(),
        }

    except FreshdeskAPIError as error:
        return {
            "error": str(error),
            "status_code": error.status_code,
            "source": get_source(),
        }


if __name__ == "__main__":
    mcp.run(transport="stdio")