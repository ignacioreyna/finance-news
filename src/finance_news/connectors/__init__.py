"""Shared connector primitives."""

from .bcra_comunicaciones_a import BcraComunicacionesAConnector
from .bora_financial import BoraFinancialConnector
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
    "BoraFinancialConnector",
    "Connector",
    "Freshness",
    "PageResult",
    "Provenance",
    "RateLimitPolicy",
    "RecoverableConnectorError",
    "RetryPolicy",
    "SourceItem",
]
