"""
Base HTTP client for Meta Muse Hatch API with RFC-7807 error translation.
"""

from typing import Any, Dict, Optional

import httpx

from muse.core.config import MuseConfig, get_config
from muse.core.exceptions import MuseApiError, NetworkError
from muse.core.logging import setup_logger

logger = setup_logger("muse.api")


def parse_rfc7807_error(response: httpx.Response) -> MuseApiError:
    """Parses RFC-7807 HatchProblemJson or fallback error response."""
    status_code = response.status_code
    try:
        data = response.json()
        return MuseApiError(
            status_code=status_code,
            title=data.get("title", f"HTTP {status_code} Error"),
            detail=data.get("detail", response.text),
            error_type=data.get("type", "about:blank"),
            error_code=data.get("error_code", ""),
            raw_data=data,
        )
    except Exception:
        return MuseApiError(
            status_code=status_code,
            title="Raw HTTP Error",
            detail=response.text,
        )


class MuseApiClient:
    """Configurable HTTP client for communicating with Hatch API."""

    def __init__(
        self,
        config: Optional[MuseConfig] = None,
        auth_token: Optional[str] = None,
    ):
        self.config = config or get_config()
        self.auth_token = auth_token

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Version": self.config.api_version,
            "User-Agent": self.config.user_agent,
        }
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        self._client = httpx.Client(
            base_url=self.config.api_base_url,
            headers=headers,
            timeout=self.config.api_timeout,
        )

    def set_auth_token(self, token: str) -> None:
        """Sets or updates the Authorization header."""
        self.auth_token = token
        self._client.headers["Authorization"] = f"Bearer {token}"

    def clear_auth_token(self) -> None:
        """Removes the Authorization header."""
        self.auth_token = None
        self._client.headers.pop("Authorization", None)

    def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """Executes an HTTP request with error parsing."""
        try:
            logger.debug(f"{method.upper()} {path} [Payload: {bool(json)}]")
            resp = self._client.request(
                method=method,
                url=path,
                json=json,
                params=params,
                headers=headers,
            )
            if resp.is_error:
                error = parse_rfc7807_error(resp)
                logger.error(f"API Error on {method} {path}: {error}")
                raise error
            return resp
        except httpx.TimeoutException as e:
            logger.error(f"Request timeout connecting to {path}: {e}")
            raise NetworkError(f"Connection timeout: {e}") from e
        except httpx.RequestError as e:
            logger.error(f"Network transport error on {path}: {e}")
            raise NetworkError(f"Network transport error: {e}") from e

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return self.request("GET", path, params=params, **kwargs)

    def post(self, path: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        return self.request("POST", path, json=json, **kwargs)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "MuseApiClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
