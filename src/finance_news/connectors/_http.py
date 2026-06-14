"""Minimal async HTTP transport contracts for connectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol


DEFAULT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True)
class HttpRequest:
    method: str
    url: str
    headers: Mapping[str, str] = field(default_factory=dict)
    params: Mapping[str, str] = field(default_factory=dict)
    body: bytes | None = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    url: str
    headers: Mapping[str, str]
    body: bytes

    def text(self, encoding: str = "utf-8") -> str:
        return self.body.decode(encoding)


class AsyncHttpTransport(Protocol):
    async def send(self, request: HttpRequest) -> HttpResponse:
        """Execute a single HTTP request."""
