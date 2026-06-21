from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import re
import unicodedata


@dataclass(frozen=True)
class CriterionResult:
    """Result for a single criterion evaluation."""
    name: str
    score: int  # 0 = falla, 1 = parcial, 2 = cumple
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "score": self.score, "note": self.note}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CriterionResult:
        return cls(name=data["name"], score=data["score"], note=data["note"])


@dataclass(frozen=True)
class ReviewResult:
    """Complete review result for a report."""
    overall_score: float  # Average of all criterion scores (0.0 to 2.0)
    per_criterion: list[CriterionResult]
    critical_failures: list[str]
    recommendations: list[str]
    approved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "per_criterion": [cr.to_dict() for cr in self.per_criterion],
            "critical_failures": self.critical_failures,
            "recommendations": self.recommendations,
            "approved": self.approved,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReviewResult:
        return cls(
            overall_score=data["overall_score"],
            per_criterion=[CriterionResult.from_dict(cr) for cr in data["per_criterion"]],
            critical_failures=data["critical_failures"],
            recommendations=data["recommendations"],
            approved=data["approved"],
        )


class ReportReviewer:
    """Reviews weekly reports against host profile rubric."""

    # Critical criteria from rubric
    CRITICAL_CRITERIA = {
        "dato_vs_lectura": "Dato vs lectura",
        "mecanismo_causal": "Mecanismo causal",
        "precio_mercado": "Precio de mercado",
        "riesgo_invalidador": "Riesgo e invalidador",
        "trazabilidad": "Trazabilidad",
    }

    # Non-critical criteria
    NON_CRITICAL_CRITERIA = {
        "intervencion_costo": "Intervencion y costo",
        "distincion_institucional": "Distincion institucional",
        "anti_narrativa": "Anti-narrativa",
        "confianza_faltantes": "Confianza y faltantes",
        "utilidad_accionable": "Utilidad accionable",
    }

    # All criteria
    ALL_CRITERIA = {**CRITICAL_CRITERIA, **NON_CRITICAL_CRITERIA}

    def __init__(self) -> None:
        pass

    def review_report(self, markdown: str) -> ReviewResult:
        """Review a markdown report and return structured evaluation."""
        results: list[CriterionResult] = []
        critical_failures: list[str] = []
        recommendations: list[str] = []

        # Normalize markdown: lowercase and remove accents for pattern matching
        def normalize_text(text: str) -> str:
            text = text.lower()
            # Remove accents
            text = unicodedata.normalize("NFKD", text)
            text = "".join(c for c in text if not unicodedata.combining(c))
            return text

        markdown_lower = normalize_text(markdown)

        # Evaluate each criterion
        results.append(self._evaluate_dato_vs_lectura(markdown, markdown_lower))
        results.append(self._evaluate_mecanismo_causal(markdown, markdown_lower))
        results.append(self._evaluate_precio_mercado(markdown, markdown_lower))
        results.append(self._evaluate_riesgo_invalidador(markdown, markdown_lower))
        results.append(self._evaluate_intervencion_costo(markdown, markdown_lower))
        results.append(self._evaluate_distincion_institucional(markdown, markdown_lower))
        results.append(self._evaluate_anti_narrativa(markdown, markdown_lower))
        results.append(self._evaluate_confianza_faltantes(markdown, markdown_lower))
        results.append(self._evaluate_trazabilidad(markdown, markdown_lower))
        results.append(self._evaluate_utilidad_accionable(markdown, markdown_lower))

        # Detect typical failures
        self._detect_overinterpretation(markdown, markdown_lower, critical_failures, recommendations)
        self._detect_missing_market_data(markdown, markdown_lower, critical_failures, recommendations)
        self._detect_bcra_tesoro_confusion(markdown, markdown_lower, critical_failures, recommendations)

        # Calculate overall score
        if results:
            overall_score = sum(cr.score for cr in results) / len(results)
        else:
            overall_score = 0.0

        # Determine approval status
        approved = self._determine_approval(results)

        return ReviewResult(
            overall_score=overall_score,
            per_criterion=results,
            critical_failures=critical_failures,
            recommendations=recommendations,
            approved=approved,
        )

    def _determine_approval(self, results: list[CriterionResult]) -> bool:
        """Determine if report is approved based on rubric decision rule."""
        critical_scores = {}
        non_critical_zero_count = 0

        for cr in results:
            criterion_key = self._get_criterion_key(cr.name)
            if criterion_key in self.CRITICAL_CRITERIA:
                critical_scores[criterion_key] = cr.score
            elif cr.score == 0:
                non_critical_zero_count += 1

        # Rejected: any critical criterion in 0
        if any(score == 0 for score in critical_scores.values()):
            return False

        # Approved: all critical criteria with 2, or single 1 as exception
        critical_values = list(critical_scores.values())
        ones_count = sum(1 for score in critical_values if score == 1)
        twos_count = sum(1 for score in critical_values if score == 2)

        if twos_count == len(critical_values):
            return True
        if twos_count == len(critical_values) - 1 and ones_count == 1:
            return True

        # Needs review: any critical criterion in 1, or two non-critical in 0
        return False

    def _get_criterion_key(self, name: str) -> str:
        """Get criterion key from display name."""
        for key, display_name in self.ALL_CRITERIA.items():
            if name == display_name:
                return key
        return name.lower().replace(" ", "_")

    def _evaluate_dato_vs_lectura(self, markdown: str, markdown_lower: str) -> CriterionResult:
        """Evaluate if facts and interpretations are clearly separated."""
        # Look for separation markers
        has_separation = any(
            pattern in markdown_lower
            for pattern in [
                "dato:",
                "hecho:",
                "lectura:",
                "interpretacion:",
                "cifra:",
                "numero:",
            ]
        )

        # Check for opinion presented as fact (warning signs)
        opinion_as_fact_patterns = [
            r"es\s+claro\s+que",
            r"es\s+evidente\s+que",
            r"no\s+hay\s+duda",
            r"indudablemente",
            r"es\s+seguro\s+que",
            r"inevitablemente",
        ]
        opinion_as_fact = any(re.search(pattern, markdown_lower) for pattern in opinion_as_fact_patterns)

        if has_separation and not opinion_as_fact:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["dato_vs_lectura"], score=2, note="Hechos y lectura claramente separados"
            )
        if has_separation and opinion_as_fact:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["dato_vs_lectura"], score=1, note="Mezcla parcial entre hecho e interpretacion"
            )
        if not has_separation and not opinion_as_fact:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["dato_vs_lectura"],
                score=1,
                note="Separacion implicita pero no explicita",
            )
        if not has_separation and opinion_as_fact:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["dato_vs_lectura"], score=0, note="Presenta opinion como hecho"
            )
        return CriterionResult(
            name=self.CRITICAL_CRITERIA["dato_vs_lectura"], score=0, note="Presenta opinion como hecho"
        )

    def _evaluate_mecanismo_causal(self, markdown: str, markdown_lower: str) -> CriterionResult:
        """Evaluate if causal mechanisms are explained."""
        # Look for mechanism explanation keywords
        mechanism_keywords = [
            "flujo",
            "caja",
            "reserva",
            "tasa",
            "posicionamiento",
            "canal",
            "transmision",
            "impacto",
            "efecto",
        ]
        mechanism_count = sum(1 for kw in mechanism_keywords if kw in markdown_lower)

        # Look for causal connectors
        causal_connectors = [
            "porque",
            "debido a",
            "dado que",
            "ya que",
            "como resultado",
            "esto genera",
            "esto provoca",
            "esto lleva",
            "a traves de",
            "mediante",
            "mejora",
            "refleja",
        ]
        causal_count = sum(1 for conn in causal_connectors if conn in markdown_lower)

        if mechanism_count >= 1 and causal_count >= 1:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["mecanismo_causal"], score=2, note="Mecanismo explicito y consistente"
            )
        if mechanism_count >= 1 or causal_count >= 1:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["mecanismo_causal"],
                score=1,
                note="Hay intuicion, pero no canal completo",
            )
        return CriterionResult(name=self.CRITICAL_CRITERIA["mecanismo_causal"], score=0, note="Relato sin mecanismo")

    def _evaluate_precio_mercado(self, markdown: str, markdown_lower: str) -> CriterionResult:
        """Evaluate if market prices are included."""
        # Look for price/variable indicators
        price_indicators = [
            "mep",
            "ccl",
            "dolar",
            "bono",
            "curva",
            "riesgo pais",
            "ust",
            "dxy",
            "oro",
            "brent",
            "wti",
            "tasa",
            "rendimiento",
            "precio",
            "variable",
            "mercado",
        ]
        price_count = sum(1 for ind in price_indicators if ind in markdown_lower)

        # Check for both confirmation and contradiction signals
        has_confirmation = any(kw in markdown_lower for kw in ["confirma", "consolida", "refuerza", "valida", "corrobora"])
        has_contradiction = any(kw in markdown_lower for kw in ["contradice", "invalida", "desmiente", "niega"])

        if price_count >= 3 and has_confirmation and has_contradiction:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["precio_mercado"],
                score=2,
                note="Confirma e invalida con precios/variables concretos",
            )
        if price_count >= 2 and (has_confirmation or has_contradiction):
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["precio_mercado"],
                score=2,
                note="Incluye precios/variables de mercado para validar la lectura",
            )
        if price_count >= 1 and (has_confirmation or has_contradiction):
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["precio_mercado"],
                score=1,
                note="Solo una de las dos o demasiado vaga",
            )
        if price_count >= 1:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["precio_mercado"],
                score=1,
                note="Menciona precios pero sin confirmacion/contradiccion clara",
            )
        return CriterionResult(name=self.CRITICAL_CRITERIA["precio_mercado"], score=0, note="Omite precio de mercado")

    def _evaluate_riesgo_invalidador(self, markdown: str, markdown_lower: str) -> CriterionResult:
        """Evaluate if risks and invalidators are exposed."""
        # Look for risk keywords
        risk_keywords = ["riesgo", "peligro", "amenaza", "vulnerabilidad", "exposicion"]
        risk_count = sum(1 for kw in risk_keywords if kw in markdown_lower)

        # Look for invalidator keywords
        invalidator_keywords = ["invalida", "rompe", "quebra", "cambia", "modifica", "altera"]
        invalidator_count = sum(1 for kw in invalidator_keywords if kw in markdown_lower)

        # Check for observable triggers
        trigger_keywords = ["senal", "gatillo", "indicador", "variable", "umbral", "limite", "si", "cuando"]
        trigger_count = sum(1 for kw in trigger_keywords if kw in markdown_lower)

        # Check for excessive certainty
        certainty_keywords = ["seguro", "cierto", "garantizado", "inevitable", "definitivo"]
        certainty_count = sum(1 for kw in certainty_keywords if kw in markdown_lower)

        if risk_count >= 1 and invalidator_count >= 1 and trigger_count >= 1 and certainty_count == 0:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["riesgo_invalidador"],
                score=2,
                note="Riesgo, senal temprana e invalidador claros",
            )
        if risk_count >= 1 and invalidator_count >= 1:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["riesgo_invalidador"],
                score=1,
                note="Riesgo generico sin disparador observable",
            )
        if certainty_count >= 2:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["riesgo_invalidador"],
                score=0,
                note="Se presenta certeza excesiva",
            )
        if risk_count >= 1:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["riesgo_invalidador"],
                score=1,
                note="Riesgo mencionado pero sin invalidador claro",
            )
        return CriterionResult(
            name=self.CRITICAL_CRITERIA["riesgo_invalidador"], score=0, note="No hay riesgo"
        )

    def _evaluate_intervencion_costo(self, markdown: str, markdown_lower: str) -> CriterionResult:
        """Evaluate if intervention and cost are clearly explained."""
        # Look for intervention keywords
        intervention_keywords = ["intervencion", "banda", "encaje", "coordinacion", "absorcion"]
        has_intervention = any(kw in markdown_lower for kw in intervention_keywords)

        if not has_intervention:
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["intervencion_costo"],
                score=2,
                note="No hay intervencion que evaluar",
            )

        # Check for the four required points
        has_instrument = any(kw in markdown_lower for kw in ["instrumento", "bono", "titulo", "letra", "nota"])
        has_channel = any(kw in markdown_lower for kw in ["canal", "mercado", "operacion", "mecanismo"])
        has_cost = any(kw in markdown_lower for kw in ["costo", "gasto", "perdida", "precio", "rendimiento"])
        has_limit = any(kw in markdown_lower for kw in ["limite", "tope", "maximo", "restriccion", "techo"])

        points_count = sum([has_instrument, has_channel, has_cost, has_limit])

        # Check for treated administered price as genuine
        admin_price_warning = any(kw in markdown_lower for kw in ["precio administrado", "precio forzado", "rendimiento artificial"])

        if admin_price_warning:
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["intervencion_costo"],
                score=0,
                note="Trata precio administrado como genuino",
            )

        if points_count == 4:
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["intervencion_costo"],
                score=2,
                note="Los cuatro puntos estan explicitados",
            )
        if points_count >= 2:
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["intervencion_costo"],
                score=1,
                note="Falta uno de los cuatro puntos",
            )
        return CriterionResult(
            name=self.NON_CRITICAL_CRITERIA["intervencion_costo"],
            score=0,
            note="Falta mas de un punto",
        )

    def _evaluate_distincion_institucional(self, markdown: str, markdown_lower: str) -> CriterionResult:
        """Evaluate if institutions are correctly distinguished."""
        # Look for institution mentions
        has_bcra = "bcra" in markdown_lower
        has_tesoro = any(kw in markdown_lower for kw in ["tesoro", "ministerio de economia", "economia"])
        has_banco = "banco" in markdown_lower
        has_mercado = "mercado" in markdown_lower

        # Check for correct attribution patterns
        correct_bcra_patterns = ["bcra.*reserva", "bcra.*tasa", "bcra.*monetario", "bcra.*emision"]
        correct_tesoro_patterns = ["tesoro.*deuda", "tesoro.*fiscal", "tesoro.*caja", "tesoro.*deficit"]

        bcra_correct = any(re.search(pattern, markdown_lower) for pattern in correct_bcra_patterns)
        tesoro_correct = any(re.search(pattern, markdown_lower) for pattern in correct_tesoro_patterns)

        institution_count = sum([has_bcra, has_tesoro, has_banco, has_mercado])

        if institution_count >= 2:
            if bcra_correct or tesoro_correct:
                return CriterionResult(
                    name=self.NON_CRITICAL_CRITERIA["distincion_institucional"],
                    score=2,
                    note="Roles y costos correctamente asignados",
                )
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["distincion_institucional"],
                score=1,
                note="Hay simplificacion tolerable",
            )
        if institution_count == 1:
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["distincion_institucional"],
                score=1,
                note="Menciona una sola institucion",
            )
        return CriterionResult(
            name=self.NON_CRITICAL_CRITERIA["distincion_institucional"],
            score=2,
            note="No aplica al contenido",
        )

    def _evaluate_anti_narrativa(self, markdown: str, markdown_lower: str) -> CriterionResult:
        """Evaluate if the report avoids epic political narrative."""
        # Look for epic/narrative language
        epic_keywords = [
            "epica",
            "heroe",
            "villano",
            "batalla",
            "guerra",
            "cruzada",
            "mision",
            "destino",
            "historica",
            "legado",
        ]
        epic_count = sum(1 for kw in epic_keywords if kw in markdown_lower)

        # Look for tribal language
        tribal_keywords = ["mercado vs gobierno", "buenos vs malos", "nosotros vs ellos", "bloque", "faccion"]
        tribal_count = sum(1 for kw in tribal_keywords if kw in markdown_lower)

        # Look for technical/operational language
        technical_keywords = [
            "flujo",
            "caja",
            "balance",
            "restriccion",
            "operativo",
            "mecanismo",
            "canal",
            "instrumento",
            "variable",
            "parametro",
        ]
        technical_count = sum(1 for kw in technical_keywords if kw in markdown_lower)

        if epic_count == 0 and tribal_count == 0 and technical_count >= 3:
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["anti_narrativa"],
                score=2,
                note="Lenguaje sobrio y tecnico",
            )
        if epic_count <= 1 and tribal_count == 0 and technical_count >= 1:
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["anti_narrativa"],
                score=1,
                note="Hay algo de narrativa, pero no domina la lectura",
            )
        if epic_count >= 2 or tribal_count >= 1:
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["anti_narrativa"],
                score=0,
                note="La narrativa reemplaza al analisis",
            )
        return CriterionResult(
            name=self.NON_CRITICAL_CRITERIA["anti_narrativa"],
            score=1,
            note="Mix sin clara dominancia",
        )

    def _evaluate_confianza_faltantes(self, markdown: str, markdown_lower: str) -> CriterionResult:
        """Evaluate if confidence and missing data are declared."""
        # Look for confidence declarations
        confidence_keywords = ["confianza alta", "confianza media", "confianza baja", "alta confianza", "media confianza", "baja confianza"]
        has_confidence = any(kw in markdown_lower for kw in confidence_keywords)

        # Look for missing data declarations
        missing_keywords = [
            "faltante",
            "no disponible",
            "sin dato",
            "informacion incompleta",
            "evidencia limitada",
            "dato faltante",
        ]
        has_missing = any(kw in markdown_lower for kw in missing_keywords)

        # Check for uncertainty acknowledgment
        uncertainty_keywords = ["incertidumbre", "limitacion", "carencia", "ausencia"]
        has_uncertainty = any(kw in markdown_lower for kw in uncertainty_keywords)

        if has_confidence and (has_missing or has_uncertainty):
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["confianza_faltantes"],
                score=2,
                note="Confianza y faltantes bien marcados",
            )
        if has_confidence or has_missing or has_uncertainty:
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["confianza_faltantes"],
                score=1,
                note="Solo uno de los dos",
            )
        return CriterionResult(
            name=self.NON_CRITICAL_CRITERIA["confianza_faltantes"],
            score=0,
            note="No reconoce limites de evidencia",
        )

    def _evaluate_trazabilidad(self, markdown: str, markdown_lower: str) -> CriterionResult:
        """Evaluate if sources can be traced."""
        # Look for source indicators
        source_patterns = [
            r"fuente:\s*\w+",
            r"bcra\s+comunica",
            r"indec\s+informa",
            r"ministerio\s+informa",
            r"seg[uú]n\s+bcra",
            r"seg[uú]n\s+indec",
            r"seg[uú]n\s+tesoro",
        ]
        source_count = sum(1 for pattern in source_patterns if re.search(pattern, markdown_lower))

        # Look for data references with context
        data_context_patterns = [
            r"\d+\.?\d*\s*%?\s+\(.*?\)",
            r"datos?\s+del?\s+\w+",
            r"estadisticas?\s+del?\s+\w+",
            r"informe?\s+del?\s+\w+",
        ]
        context_count = sum(1 for pattern in data_context_patterns if re.search(pattern, markdown_lower))

        # Check for proxy mentions
        proxy_keywords = ["proxy", "estimacion", "aproximacion", "senal", "indicador"]
        has_proxy = any(kw in markdown_lower for kw in proxy_keywords)

        if source_count >= 2 and context_count >= 1:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["trazabilidad"],
                score=2,
                note="Usa fuentes primarias o proxies explicitados",
            )
        if source_count >= 1 and context_count >= 1:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["trazabilidad"],
                score=2,
                note="Usa fuentes primarias o proxies explicitados",
            )
        if source_count >= 1 or context_count >= 1 or has_proxy:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["trazabilidad"],
                score=1,
                note="Algunas afirmaciones quedan sin respaldo directo",
            )
        return CriterionResult(name=self.CRITICAL_CRITERIA["trazabilidad"], score=0, note="No se puede auditar la lectura")

        # Check for proxy mentions
        proxy_keywords = ["proxy", "estimacion", "aproximacion", "señal", "indicador"]
        has_proxy = any(kw in markdown_lower for kw in proxy_keywords)

        if source_count >= 2 and context_count >= 2:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["trazabilidad"],
                score=2,
                note="Usa fuentes primarias o proxies explicitados",
            )
        if source_count >= 1 or context_count >= 1 or has_proxy:
            return CriterionResult(
                name=self.CRITICAL_CRITERIA["trazabilidad"],
                score=1,
                note="Algunas afirmaciones quedan sin respaldo directo",
            )
        return CriterionResult(name=self.CRITICAL_CRITERIA["trazabilidad"], score=0, note="No se puede auditar la lectura")

    def _evaluate_utilidad_accionable(self, markdown: str, markdown_lower: str) -> CriterionResult:
        """Evaluate if actionable recommendations are provided."""
        # Look for actionable follow-up keywords
        actionable_keywords = [
            "mirar",
            "seguir",
            "observar",
            "monitorear",
            "vigilar",
            "atender",
            "controlar",
            "proxima semana",
            "semana que viene",
            "gatillo",
            "trigger",
        ]
        actionable_count = sum(1 for kw in actionable_keywords if kw in markdown_lower)

        # Look for specific variables to follow
        variable_patterns = [
            r"seguir\s+\w+",
            r"mirar\s+\w+",
            r"observar\s+\w+",
            r"monitorear\s+\w+",
            r"vigilar\s+\w+",
        ]
        variable_count = sum(1 for pattern in variable_patterns if re.search(pattern, markdown_lower))

        # Look for agenda/next steps
        agenda_keywords = ["agenda", "proximo paso", "siguiente", "a venir", "futuro"]
        has_agenda = any(kw in markdown_lower for kw in agenda_keywords)

        if actionable_count >= 1 and variable_count >= 1:
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["utilidad_accionable"],
                score=2,
                note="Hay gatillos concretos de seguimiento",
            )
        if actionable_count >= 1 or variable_count >= 1 or has_agenda:
            return CriterionResult(
                name=self.NON_CRITICAL_CRITERIA["utilidad_accionable"],
                score=1,
                note="Recomendacion generica",
            )
        return CriterionResult(
            name=self.NON_CRITICAL_CRITERIA["utilidad_accionable"],
            score=0,
            note="No deja agenda verificable",
        )

    def _detect_overinterpretation(
        self, markdown: str, markdown_lower: str, critical_failures: list[str], recommendations: list[str]
    ) -> None:
        """Detect over-interpretation of data points."""
        # Look for strong causal claims without supporting figures
        overinterpretation_patterns = [
            r"cambio\s+de\s+regimen",
            r"cambio\s+estructural",
            r"punto\s+de\s+inflexion",
            r"nueva\s+etapa",
            r"paradigma\s+nuevo",
        ]

        for pattern in overinterpretation_patterns:
            if re.search(pattern, markdown_lower):
                # Check if there's supporting numerical evidence nearby
                has_figure = bool(re.search(r"\d+\.?\d*\s*%?", markdown_lower))
                if not has_figure:
                    # Get the matched text for better error message
                    match = re.search(pattern, markdown_lower)
                    if match:
                        matched_text = match.group(0)
                        critical_failures.append(f"Sobreinterpretacion detectada: '{matched_text}' sin cifras de respaldo")
                        recommendations.append("Apojar conclusiones estructurales con datos consensuados y persistencia")
                break

    def _detect_missing_market_data(
        self, markdown: str, markdown_lower: str, critical_failures: list[str], recommendations: list[str]
    ) -> None:
        """Detect missing market price data."""
        # Look for credibility/risk claims without market evidence
        claim_patterns = [
            r"credibilidad.*mejor[oa]",
            r"riesgo.*sube",
            r"riesgo.*baj[oa]",
            r"confianza.*aumenta",
            r"incertidumbre.*reduce",
        ]

        market_variables = ["mep", "ccl", "dolar", "bono", "curva", "riesgo pais", "ust", "dxy", "tasa", "rendimiento"]

        for pattern in claim_patterns:
            if re.search(pattern, markdown_lower):
                # Check if there's market variable mentioned
                has_market_var = any(var in markdown_lower for var in market_variables)
                if not has_market_var:
                    # Get the matched text for better error message
                    match = re.search(pattern, markdown_lower)
                    if match:
                        matched_text = match.group(0)
                        critical_failures.append(f"Reclamo de credibilidad/riesgo sin variable de mercado: '{matched_text}'")
                        recommendations.append("Incluir variable de mercado (MEP, CCL, curva, riesgo pais, etc.) para validar el reclamo")
                break

    def _detect_bcra_tesoro_confusion(
        self, markdown: str, markdown_lower: str, critical_failures: list[str], recommendations: list[str]
    ) -> None:
        """Detect BCRA vs Tesoro confusion."""
        # Look for BCRA attributed with fiscal/debt terms
        bcra_confusion_patterns = [
            r"bcra.*deuda",
            r"bcra.*fiscal",
            r"bcra.*deficit",
            r"bcra.*impositivo",
            r"bcra.*gasto",
        ]

        # Look for Tesoro attributed with monetary/reserve terms
        tesoro_confusion_patterns = [
            r"tesoro.*reserva",
            r"tesoro.*monetario",
            r"tesoro.*emision",
            r"tesoro.*tasa",
            r"econom[íi]a.*reserva",
        ]

        for pattern in bcra_confusion_patterns:
            if re.search(pattern, markdown_lower):
                critical_failures.append(f"Posible confusion: BCRA con terminos fiscales: '{pattern}'")
                recommendations.append("Verificar que deuda y deficit sean atribuidos al Tesoro, no al BCRA")
                break

        for pattern in tesoro_confusion_patterns:
            if re.search(pattern, markdown_lower):
                critical_failures.append(f"Posible confusion: Tesoro con terminos monetarios: '{pattern}'")
                recommendations.append("Verificar que reservas y politica monetaria sean atribuidas al BCRA, no al Tesoro")
                break


def review_report(markdown: str) -> ReviewResult:
    """Convenience function to review a markdown report."""
    reviewer = ReportReviewer()
    return reviewer.review_report(markdown)