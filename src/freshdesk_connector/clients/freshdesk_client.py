import time
from typing import Any, Callable

import httpx


class FreshdeskAPIError(Exception):
    """Raised when the Freshdesk API returns an error."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code


class FreshdeskClient:
    """HTTP client for the Freshdesk REST API."""

    def __init__(
        self,
        domain: str,
        api_key: str,
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
        if not domain:
            raise ValueError("Freshdesk domain is required.")

        if not api_key:
            raise ValueError("Freshdesk API key is required.")

        if max_retries < 0:
            raise ValueError("max_retries cannot be negative.")

        if backoff_factor < 0:
            raise ValueError("backoff_factor cannot be negative.")

        self.base_url = f"https://{domain}/api/v2"
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.sleep_fn = sleep_fn

        self.client = httpx.Client(
            base_url=self.base_url,
            auth=(api_key, "X"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=timeout,
        )

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Perform an authenticated GET request with rate-limit retries."""

        for attempt in range(self.max_retries + 1):
            response = self.client.get(
                path,
                params=params,
            )

            if response.status_code == 429:
                if attempt >= self.max_retries:
                    raise FreshdeskAPIError(
                        "Freshdesk API rate limit exceeded "
                        "after maximum retries.",
                        status_code=429,
                    )

                retry_after = self._get_retry_after(response)

                if retry_after is None:
                    retry_after = self.backoff_factor * (2**attempt)

                self.sleep_fn(retry_after)
                continue

            if response.status_code >= 400:
                raise FreshdeskAPIError(
                    f"Freshdesk API request failed: "
                    f"{response.status_code} {response.text}",
                    status_code=response.status_code,
                )

            return response.json()

        raise FreshdeskAPIError(
            "Freshdesk API request failed after retries."
        )

    @staticmethod
    def _get_retry_after(
        response: httpx.Response,
    ) -> float | None:
        """Read Retry-After header if it contains a numeric value."""

        value = response.headers.get("Retry-After")

        if value is None:
            return None

        try:
            return float(value)
        except ValueError:
            return None

    def close(self) -> None:
        """Close the HTTP client."""

        self.client.close()