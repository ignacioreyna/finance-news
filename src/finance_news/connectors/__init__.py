"""Shared connector primitives."""

from .bcra_catalogo import BcraCatalogoConnector
from .bcra_comunicaciones_a import BcraComunicacionesAConnector
from .bcra_dolar_oficial import BcraDolarOficialConnector
from .bcra_tasas_cer_tamar import BcraTasasCerTamarConnector
from .bcra_variables_reservas import BcraVariablesReservasConnector
from .bora_financial import BoraFinancialConnector
from .indec_ipc import IndecIpcConnector
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
    "bcra_catalogo": BcraCatalogoConnector,
    "bcra_comunicaciones_a": BcraComunicacionesAConnector,
    "bcra_dolar_oficial": BcraDolarOficialConnector,
    "bcra_tasas_cer_tamar": BcraTasasCerTamarConnector,
    "bcra_variables_reservas": BcraVariablesReservasConnector,
    "bora_financial": BoraFinancialConnector,
    "indec_ipc": IndecIpcConnector,
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
    "BcraCatalogoConnector",
    "BcraComunicacionesAConnector",
    "BcraDolarOficialConnector",
    "BcraTasasCerTamarConnector",
    "BcraVariablesReservasConnector",
    "BoraFinancialConnector",
    "Connector",
    "Freshness",
    "IndecIpcConnector",
    "PageResult",
    "Provenance",
    "RateLimitPolicy",
    "RecoverableConnectorError",
    "RetryPolicy",
    "SourceItem",
    "available_connectors",
    "get_connector",
]
