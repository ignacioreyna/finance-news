"""Shared connector primitives."""

from .bcra_balance_cambiario import BcraBalanceCambiarioConnector
from .bcra_calendario import BcraCalendarioConnector
from .bcra_catalogo import BcraCatalogoConnector
from .bcra_comunicaciones_a import BcraComunicacionesAConnector
from .bcra_dolar_oficial import BcraDolarOficialConnector
from .bcra_tasas_cer_tamar import BcraTasasCerTamarConnector
from .bcra_variables_reservas import BcraVariablesReservasConnector
from .bea_personal_income import BeaPersonalIncomeConnector
from .bea_real_gdp import BeaRealGdpConnector
from .bls_timeseries import BlsTimeseriesConnector
from .bora_financial import BoraFinancialConnector
from .datosgobar_fiscal import DatosgobarFiscalConnector
from .dol_weekly_claims import DolWeeklyClaimsConnector
from .eia_wpsr import EiaWpsrConnector
from .fed_h41_liquidity import FedH41LiquidityConnector
from .fomc_calendario import FomcCalendarioConnector
from .fed_speeches import FedSpeechesConnector
from .fomc_minutes import FomcMinutesConnector
from .fomc_sep import FomcSepConnector
from .fomc_statements import FomcStatementsConnector
from .fred_market_proxies import FredMarketProxiesConnector
from .indec_calendario import IndecCalendarioConnector
from .indec_ipc import IndecIpcConnector
from .nyfed_repo import NyfedRepoConnector
from .nyfed_sofr import NyfedSofrConnector
from .nyfed_soma import NyfedSomaConnector
from .opec_eventos import OpecEventosConnector
from .tesoro_licitaciones import TesoroLicitacionesConnector
from .treasury_dts_cashflows import TreasuryDtsCashflowsConnector
from .treasury_dts_tga import TreasuryDtsTgaConnector
from .treasurydirect_auctions import TreasurydirectAuctionsConnector
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
    "bea_personal_income": BeaPersonalIncomeConnector,
    "bea_real_gdp": BeaRealGdpConnector,
    "bls_timeseries": BlsTimeseriesConnector,
    "bora_financial": BoraFinancialConnector,
    "datosgobar_fiscal": DatosgobarFiscalConnector,
    "dol_weekly_claims": DolWeeklyClaimsConnector,
    "eia_wpsr": EiaWpsrConnector,
    "fed_h41_liquidity": FedH41LiquidityConnector,
    "fed_speeches": FedSpeechesConnector,
    "fomc_calendario": FomcCalendarioConnector,
    "fomc_minutes": FomcMinutesConnector,
    "fomc_sep": FomcSepConnector,
    "fomc_statements": FomcStatementsConnector,
    "fred_market_proxies": FredMarketProxiesConnector,
    "indec_calendario": IndecCalendarioConnector,
    "indec_ipc": IndecIpcConnector,
    "nyfed_repo": NyfedRepoConnector,
    "nyfed_sofr": NyfedSofrConnector,
    "nyfed_soma": NyfedSomaConnector,
    "opec_eventos": OpecEventosConnector,
    "tesoro_licitaciones": TesoroLicitacionesConnector,
    "treasury_dts_cashflows": TreasuryDtsCashflowsConnector,
    "treasury_dts_tga": TreasuryDtsTgaConnector,
    "treasurydirect_auctions": TreasurydirectAuctionsConnector,
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
    "BeaPersonalIncomeConnector",
    "BeaRealGdpConnector",
    "BlsTimeseriesConnector",
    "BoraFinancialConnector",
    "Connector",
    "DatosgobarFiscalConnector",
    "DolWeeklyClaimsConnector",
    "EiaWpsrConnector",
    "FedH41LiquidityConnector",
    "FedSpeechesConnector",
    "FomcCalendarioConnector",
    "FomcMinutesConnector",
    "FomcSepConnector",
    "FomcStatementsConnector",
    "FredMarketProxiesConnector",
    "Freshness",
    "IndecCalendarioConnector",
    "IndecIpcConnector",
    "NyfedRepoConnector",
    "NyfedSofrConnector",
    "NyfedSomaConnector",
    "OpecEventosConnector",
    "PageResult",
    "Provenance",
    "RateLimitPolicy",
    "RecoverableConnectorError",
    "RetryPolicy",
    "SourceItem",
    "TesoroLicitacionesConnector",
    "TreasuryDtsCashflowsConnector",
    "TreasuryDtsTgaConnector",
    "TreasurydirectAuctionsConnector",
    "available_connectors",
    "get_connector",
]
