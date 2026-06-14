"""Shared connector primitives."""

from .bcra_comunicaciones_a import BcraComunicacionesAConnector
from .models import (
    Connector,
    Freshness,
    PageResult,
    Provenance,
    RateLimitPolicy,
    RecoverableConnectorError,
    RetryPolicy,
    SourceItem,
)

__all__ = [
    "BcraComunicacionesAConnector",
    "Connector",
    "Freshness",
    "PageResult",
    "Provenance",
    "RateLimitPolicy",
    "RecoverableConnectorError",
    "RetryPolicy",
    "SourceItem",
]
