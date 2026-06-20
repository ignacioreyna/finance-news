"""Shared connector primitives."""

from .bcra_balance_cambiario import BcraBalanceCambiarioConnector
from .bcra_calendario import BcraCalendarioConnector
from .bcra_catalogo import BcraCatalogoConnector
from .bcra_comunicaciones_a import BcraComunicacionesAConnector
from .bcra_dolar_oficial import BcraDolarOficialConnector
from .bcra_tasas_cer_tamar import BcraTasasCerTamarConnector
from .bcra_variables_reservas import BcraVariablesReservasConnector
from .bora_financial import BoraFinancialConnector
from .datosgobar_fiscal import DatosgobarFiscalConnector
from .dol_weekly_claims import DolWeeklyClaimsConnector
from .fomc_calendario import FomcCalendarioConnector
from .indec_calendario import IndecCalendarioConnector
from .indec_ipc import IndecIpcConnector
from .nyfed_sofr import NyfedSofrConnector
from .tesoro_licitaciones import TesoroLicitacionesConnector
from .treasury_dts_tga import TreasuryDtsTgaConnector
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
    "bcra_balance_cambiario": BcraBalanceCambiarioConnector,
    "bcra_calendario": BcraCalendarioConnector,
    "bcra_catalogo": BcraCatalogoConnector,
    "bcra_comunicaciones_a": BcraComunicacionesAConnector,
    "bcra_dolar_oficial": BcraDolarOficialConnector,
    "bcra_tasas_cer_tamar": BcraTasasCerTamarConnector,
    "bcra_variables_reservas": BcraVariablesReservasConnector,
    "bora_financial": BoraFinancialConnector,
    "datosgobar_fiscal": DatosgobarFiscalConnector,
    "dol_weekly_claims": DolWeeklyClaimsConnector,
    "fomc_calendario": FomcCalendarioConnector,
    "indec_calendario": IndecCalendarioConnector,
    "indec_ipc": IndecIpcConnector,
    "nyfed_sofr": NyfedSofrConnector,
    "tesoro_licitaciones": TesoroLicitacionesConnector,
    "treasury_dts_tga": TreasuryDtsTgaConnector,
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
    "BcraBalanceCambiarioConnector",
    "BcraCalendarioConnector",
    "BcraCatalogoConnector",
    "BcraComunicacionesAConnector",
    "BcraDolarOficialConnector",
    "BcraTasasCerTamarConnector",
    "BcraVariablesReservasConnector",
    "BoraFinancialConnector",
    "Connector",
    "DatosgobarFiscalConnector",
    "DolWeeklyClaimsConnector",
    "FomcCalendarioConnector",
    "Freshness",
    "IndecCalendarioConnector",
    "IndecIpcConnector",
    "NyfedSofrConnector",
    "PageResult",
    "Provenance",
    "RateLimitPolicy",
    "RecoverableConnectorError",
    "RetryPolicy",
    "SourceItem",
    "TesoroLicitacionesConnector",
    "TreasuryDtsTgaConnector",
    "available_connectors",
    "get_connector",
]
