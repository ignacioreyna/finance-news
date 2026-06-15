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

# Connector registry: name -> connector class
_CONNECTORS: dict[str, type[Connector]] = {
    "bcra_comunicaciones_a": BcraComunicacionesAConnector,
    "bora_financial": BoraFinancialConnector,
}


def available_connectors() -> list[str]:
    """Return list of available connector names."""
    return list(_CONNECTORS.keys())


def get_connector(name: str) -> type[Connector]:
    """Get connector class by name.

    Args:
        name: Connector name.

    Returns:
        Connector class.

    Raises:
        KeyError: If connector name is unknown.
    """
    return _CONNECTORS[name]


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
    "available_connectors",
    "get_connector",
]
