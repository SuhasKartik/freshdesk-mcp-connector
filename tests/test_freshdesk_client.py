import httpx
import pytest

from freshdesk_connector.clients.freshdesk_client import (
    FreshdeskAPIError,
    FreshdeskClient,
)


def make_client(handler):
    """Create a Freshdesk client using a mocked HTTP transport."""

    client = FreshdeskClient(
        domain="example.freshdesk.com",
        api_key="test-api-key",
    )

    client.client.close()

    client.client = httpx.Client(
        base_url=client.base_url,
        auth=("test-api-key", "X"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        transport=httpx.MockTransport(handler),
    )

    return client


def test_successful_get_request():
    def handler(request):
        assert request.url.path == "/api/v2/tickets/1001"

        return httpx.Response(
            200,
            json={
                "id": 1001,
                "subject": "Unable to log in",
                "status": 2,
            },
        )

    client = make_client(handler)

    try:
        result = client.get("/tickets/1001")

        assert result["id"] == 1001
        assert result["subject"] == "Unable to log in"
    finally:
        client.close()


def test_authentication_error():
    def handler(request):
        return httpx.Response(
            401,
            json={"message": "Authentication failed"},
        )

    client = make_client(handler)

    try:
        with pytest.raises(FreshdeskAPIError) as exc_info:
            client.get("/tickets/1001")

        assert exc_info.value.status_code == 401
    finally:
        client.close()


def test_forbidden_error():
    def handler(request):
        return httpx.Response(
            403,
            json={"message": "Access denied"},
        )

    client = make_client(handler)

    try:
        with pytest.raises(FreshdeskAPIError) as exc_info:
            client.get("/tickets/1001")

        assert exc_info.value.status_code == 403
    finally:
        client.close()


def test_not_found_error():
    def handler(request):
        return httpx.Response(
            404,
            json={"message": "Ticket not found"},
        )

    client = make_client(handler)

    try:
        with pytest.raises(FreshdeskAPIError) as exc_info:
            client.get("/tickets/9999")

        assert exc_info.value.status_code == 404
    finally:
        client.close()


def test_rate_limit_error():
    def handler(request):
        return httpx.Response(
            429,
            headers={"Retry-After": "10"},
            json={"message": "Rate limit exceeded"},
        )

    client = make_client(handler)

    try:
        with pytest.raises(FreshdeskAPIError) as exc_info:
            client.get("/tickets")

        assert exc_info.value.status_code == 429
    finally:
        client.close()


def test_server_error():
    def handler(request):
        return httpx.Response(
            500,
            json={"message": "Internal server error"},
        )

    client = make_client(handler)

    try:
        with pytest.raises(FreshdeskAPIError) as exc_info:
            client.get("/tickets")

        assert exc_info.value.status_code == 500
    finally:
        client.close()


def test_missing_domain_is_rejected():
    with pytest.raises(ValueError):
        FreshdeskClient(
            domain="",
            api_key="test-api-key",
        )


def test_missing_api_key_is_rejected():
    with pytest.raises(ValueError):
        FreshdeskClient(
            domain="example.freshdesk.com",
            api_key="",
        )

def test_rate_limit_retries_then_succeeds():
    attempts = 0
    sleep_times = []

    def handler(request):
        nonlocal attempts

        attempts += 1

        if attempts < 3:
            return httpx.Response(
                429,
                headers={"Retry-After": "2"},
                json={"message": "Rate limit exceeded"},
            )

        return httpx.Response(
            200,
            json={
                "id": 1001,
                "subject": "Unable to log in",
            },
        )

    def fake_sleep(seconds):
        sleep_times.append(seconds)

    client = FreshdeskClient(
        domain="example.freshdesk.com",
        api_key="test-api-key",
        max_retries=3,
        sleep_fn=fake_sleep,
    )

    client.client.close()

    client.client = httpx.Client(
        base_url=client.base_url,
        auth=("test-api-key", "X"),
        transport=httpx.MockTransport(handler),
    )

    try:
        result = client.get("/tickets/1001")

        assert result["id"] == 1001
        assert attempts == 3
        assert sleep_times == [2.0, 2.0]
    finally:
        client.close()


def test_rate_limit_uses_exponential_backoff_without_header():
    attempts = 0
    sleep_times = []

    def handler(request):
        nonlocal attempts

        attempts += 1

        if attempts < 4:
            return httpx.Response(
                429,
                json={"message": "Rate limit exceeded"},
            )

        return httpx.Response(
            200,
            json={"id": 1001},
        )

    def fake_sleep(seconds):
        sleep_times.append(seconds)

    client = FreshdeskClient(
        domain="example.freshdesk.com",
        api_key="test-api-key",
        max_retries=3,
        backoff_factor=1.0,
        sleep_fn=fake_sleep,
    )

    client.client.close()

    client.client = httpx.Client(
        base_url=client.base_url,
        auth=("test-api-key", "X"),
        transport=httpx.MockTransport(handler),
    )

    try:
        result = client.get("/tickets/1001")

        assert result["id"] == 1001
        assert attempts == 4
        assert sleep_times == [1.0, 2.0, 4.0]
    finally:
        client.close()


def test_rate_limit_fails_after_max_retries():
    attempts = 0
    sleep_times = []

    def handler(request):
        nonlocal attempts

        attempts += 1

        return httpx.Response(
            429,
            json={"message": "Rate limit exceeded"},
        )

    def fake_sleep(seconds):
        sleep_times.append(seconds)

    client = FreshdeskClient(
        domain="example.freshdesk.com",
        api_key="test-api-key",
        max_retries=2,
        backoff_factor=1.0,
        sleep_fn=fake_sleep,
    )

    client.client.close()

    client.client = httpx.Client(
        base_url=client.base_url,
        auth=("test-api-key", "X"),
        transport=httpx.MockTransport(handler),
    )

    try:
        with pytest.raises(FreshdeskAPIError) as exc_info:
            client.get("/tickets/1001")

        assert exc_info.value.status_code == 429
        assert attempts == 3
        assert sleep_times == [1.0, 2.0]
    finally:
        client.close()