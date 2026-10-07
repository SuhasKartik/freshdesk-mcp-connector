from pydantic import BaseModel, Field


class Ticket(BaseModel):
    """Normalized representation of a support ticket."""

    id: int
    subject: str
    description: str
    status: str
    priority: str
    requester: str


class TicketSearchResult(BaseModel):
    """Result returned from a ticket search."""

    total: int
    tickets: list[Ticket]
    source: str