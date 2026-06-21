from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from finance_news.connectors.models import SourceItem
from finance_news.scoring import ScoredSignal


@dataclass(frozen=True)
class ContextPackItem:
    """A selected item with its score, confidence, source ref, and excerpt."""

    topic: str
    score: int
    fact: str
    interpretation: str
    mechanism: str
    confirm_variable: str
    invalidate_variable: str
    confidence: str
    source_ids: list[str]
    excerpt: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tema": self.topic,
            "score": self.score,
            "dato": self.fact,
            "lectura": self.interpretation,
            "mecanismo": self.mechanism,
            "precio_o_variable_que_confirma": self.confirm_variable,
            "precio_o_variable_que_invalida": self.invalidate_variable,
            "confianza": self.confidence,
            "fuente_ids": self.source_ids,
            "extracto": self.excerpt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextPackItem":
        """Create from dictionary."""
        return cls(
            topic=data["tema"],
            score=data["score"],
            fact=data["dato"],
            interpretation=data["lectura"],
            mechanism=data["mecanismo"],
            confirm_variable=data["precio_o_variable_que_confirma"],
            invalidate_variable=data["precio_o_variable_que_invalida"],
            confidence=data["confianza"],
            source_ids=data["fuente_ids"],
            excerpt=data.get("extracto", ""),
        )


@dataclass(frozen=True)
class SourceIndexEntry:
    """Source index entry for traceability."""

    id: str
    label: str
    type: str
    region: str
    url: str
    published_at: str | None
    accessed_at: str
    supports: list[str]
    confidence_impact: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "region": self.region,
            "url": self.url,
            "published_at": self.published_at,
            "accessed_at": self.accessed_at,
            "supports": self.supports,
            "confidence_impact": self.confidence_impact,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceIndexEntry":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            label=data["label"],
            type=data["type"],
            region=data["region"],
            url=data["url"],
            published_at=data.get("published_at"),
            accessed_at=data["accessed_at"],
            supports=data["supports"],
            confidence_impact=data["confidence_impact"],
        )


@dataclass(frozen=True)
class OpenGap:
    """Represents a missing input or gap in the context pack."""

    section: str
    missing_input: str
    fallback_used: str | None
    confidence_adjustment: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "section": self.section,
            "missing_input": self.missing_input,
            "fallback_used": self.fallback_used,
            "confidence_adjustment": self.confidence_adjustment,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OpenGap":
        """Create from dictionary."""
        return cls(
            section=data["section"],
            missing_input=data["missing_input"],
            fallback_used=data.get("fallback_used"),
            confidence_adjustment=data["confidence_adjustment"],
            note=data["note"],
        )


@dataclass(frozen=True)
class ReportContextPack:
    """Complete report context pack with metadata, items, sources, and gaps."""

    week_end_date: str
    generated_at: str
    timezone: str
    argentina_items: list[ContextPackItem]
    international_items: list[ContextPackItem]
    market_items: list[ContextPackItem]
    source_index: list[SourceIndexEntry]
    open_gaps: list[OpenGap]
    summary_stats: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "reporting_window": {
                "week_end_date": self.week_end_date,
                "timezone": self.timezone,
                "calendar_mode": "weekly_close",
            },
            "generator_profile": {
                "target_model": "medium",
                "language": "es-AR",
                "audience": "inversor/macroeconomico",
                "host_style": {
                    "tone": "tecnico, directo, coloquial",
                    "bias": "liberal-institucional pragmatica",
                    "priority": [
                        "mecanismo antes que relato",
                        "dato vs expectativa vs precio",
                        "riesgo e invalidador",
                        "trazabilidad auditable",
                    ],
                },
            },
            "editorial_rules": {
                "must_separate_fact_and_interpretation": True,
                "must_include_confirmation_variable": True,
                "must_include_invalidation_variable": True,
                "must_flag_intervention_cost_limit": True,
                "must_declare_confidence": True,
            },
            "source_policy": {
                "primary_required_when_available": True,
                "secondary_allowed_as_proxy": True,
                "secondary_requires_lower_confidence": True,
                "max_unverified_claims_per_section": 0,
            },
            "signal_selection": {
                "include_threshold": 2,
                "lead_threshold": 3,
                "scenario_break_threshold": 4,
            },
            "sections": {
                "argentina": {
                    "inflacion_y_actividad": [item.to_dict() for item in self.argentina_items],
                },
                "internacional": {
                    "geopolitica": [item.to_dict() for item in self.international_items],
                },
                "mercado": {
                    "fx": [item.to_dict() for item in self.market_items],
                },
            },
            "source_index": [entry.to_dict() for entry in self.source_index],
            "open_gaps": [gap.to_dict() for gap in self.open_gaps],
            "summary_stats": self.summary_stats,
            "generated_at": self.generated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ReportContextPack":
        """Create from dictionary."""
        window = data["reporting_window"]
        sections = data["sections"]
        return cls(
            week_end_date=window["week_end_date"],
            timezone=window["timezone"],
            generated_at=data["generated_at"],
            argentina_items=[ContextPackItem.from_dict(item) for item in sections["argentina"]["inflacion_y_actividad"]],
            international_items=[ContextPackItem.from_dict(item) for item in sections["internacional"]["geopolitica"]],
            market_items=[ContextPackItem.from_dict(item) for item in sections["mercado"]["fx"]],
            source_index=[SourceIndexEntry.from_dict(entry) for entry in data["source_index"]],
            open_gaps=[OpenGap.from_dict(gap) for gap in data["open_gaps"]],
            summary_stats=data["summary_stats"],
        )


class ContextPackBuilder:
    """Builds a weekly report context pack from SourceItems + scores + sources + open gaps."""

    DEFAULT_SCORE_THRESHOLD: int = 2
    DEFAULT_CONFIDENCE_THRESHOLD: str = "media"

    def __init__(
        self,
        score_threshold: int = DEFAULT_SCORE_THRESHOLD,
        confidence_threshold: str = DEFAULT_CONFIDENCE_THRESHOLD,
    ) -> None:
        """Initialize the builder with inclusion thresholds."""
        self.score_threshold = score_threshold
        self.confidence_threshold = confidence_threshold

    def _calculate_confidence(self, scored_signal: ScoredSignal, source_item: SourceItem) -> str:
        """Calculate confidence level based on score and source quality."""
        if scored_signal.score >= 4 and source_item.source == "primaria_oficial":
            return "alta"
        elif scored_signal.score >= 3:
            return "alta"
        elif scored_signal.score >= 2:
            return "media"
        else:
            return "baja"

    def _determine_region(self, signal_domain: str, signal_region: str) -> str:
        """Determine if an item is argentina, international, or market."""
        if signal_region == "argentina":
            if signal_domain in ["tesoro_y_deuda", "bcra_reservas", "cambiario"]:
                return "mercado"
            else:
                return "argentina"
        else:
            return "internacional"

    def _create_source_index_entry(
        self,
        source_item: SourceItem,
        scored_signal: ScoredSignal,
        confidence: str,
        entry_id: str,
    ) -> SourceIndexEntry:
        """Create a source index entry from a SourceItem."""
        supports = [f"{scored_signal.signal.domain}[{entry_id}]"]
        confidence_impact = "none" if confidence == "alta" else "lower"
        return SourceIndexEntry(
            id=entry_id,
            label=f"{source_item.source} - {source_item.title[:50]}",
            type="primaria_oficial" if source_item.source == "primaria_oficial" else "secundaria",
            region=scored_signal.signal.region,
            url=source_item.url,
            published_at=source_item.published_at.isoformat() if source_item.published_at else None,
            accessed_at=source_item.freshness.fetched_at.isoformat(),
            supports=supports,
            confidence_impact=confidence_impact,
        )

    def _create_context_pack_item(
        self,
        scored_signal: ScoredSignal,
        source_item: SourceItem,
        source_id: str,
        confidence: str,
    ) -> ContextPackItem:
        """Create a context pack item from a scored signal and source."""
        excerpt = source_item.summary[:100] if source_item.summary else ""
        if not excerpt and source_item.body:
            excerpt = source_item.body[:100]
        return ContextPackItem(
            topic=scored_signal.signal.name,
            score=scored_signal.score,
            fact=f"{scored_signal.signal.value} {scored_signal.signal.unit}",
            interpretation=scored_signal.rationale,
            mechanism=f"Canal: {scored_signal.signal.domain}",
            confirm_variable=f"{scored_signal.signal.name} confirma",
            invalidate_variable=f"{scored_signal.signal.name} invalida",
            confidence=confidence,
            source_ids=[source_id],
            excerpt=excerpt,
        )

    def _apply_inclusion_rules(
        self,
        scored_signal: ScoredSignal,
        source_item: SourceItem,
        confidence: str,
    ) -> tuple[bool, str | None]:
        """Apply inclusion rules and return (include, exclusion_reason)."""
        if scored_signal.score < self.score_threshold:
            return False, f"Score {scored_signal.score} below threshold {self.score_threshold}"

        confidence_order = {"alta": 3, "media": 2, "baja": 1}
        if confidence_order.get(confidence, 0) < confidence_order.get(self.confidence_threshold, 0):
            return False, f"Confidence {confidence} below threshold {self.confidence_threshold}"

        return True, None

    def build(
        self,
        items: list[SourceItem],
        scored_signals: list[ScoredSignal],
        week_end_date: str,
        *,
        generated_at: str | None = None,
        timezone: str = "America/Argentina/Buenos_Aires",
    ) -> ReportContextPack:
        """Build a report context pack from items and scored signals."""
        if generated_at is None:
            generated_at = datetime.now().isoformat()

        argentina_items: list[ContextPackItem] = []
        international_items: list[ContextPackItem] = []
        market_items: list[ContextPackItem] = []
        source_index: list[SourceIndexEntry] = []
        open_gaps: list[OpenGap] = []

        item_map = {item.external_id: item for item in items}

        for idx, scored_signal in enumerate(scored_signals):
            signal_id = scored_signal.signal.domain + "_" + str(idx)
            source_item = item_map.get(scored_signal.signal.name, None)

            if source_item is None:
                open_gaps.append(
                    OpenGap(
                        section=scored_signal.signal.domain,
                        missing_input=f"SourceItem for {scored_signal.signal.name}",
                        fallback_used=None,
                        confidence_adjustment="baja",
                        note="No source item found for this signal",
                    )
                )
                continue

            confidence = self._calculate_confidence(scored_signal, source_item)
            include, exclusion_reason = self._apply_inclusion_rules(scored_signal, source_item, confidence)

            if not include:
                open_gaps.append(
                    OpenGap(
                        section=scored_signal.signal.domain,
                        missing_input=f"Signal with score {scored_signal.score}",
                        fallback_used=None,
                        confidence_adjustment="baja",
                        note=exclusion_reason or "Excluded by inclusion rules",
                    )
                )
                continue

            source_index_entry = self._create_source_index_entry(source_item, scored_signal, confidence, f"src_{idx}")
            source_index.append(source_index_entry)

            context_item = self._create_context_pack_item(scored_signal, source_item, f"src_{idx}", confidence)

            region = self._determine_region(scored_signal.signal.domain, scored_signal.signal.region)
            if region == "argentina":
                argentina_items.append(context_item)
            elif region == "internacional":
                international_items.append(context_item)
            else:
                market_items.append(context_item)

        total_included = len(argentina_items) + len(international_items) + len(market_items)
        summary_stats = {
            "total_signals": len(scored_signals),
            "included_signals": total_included,
            "excluded_signals": len(open_gaps),
            "argentina_count": len(argentina_items),
            "international_count": len(international_items),
            "market_count": len(market_items),
            "source_count": len(source_index),
        }

        return ReportContextPack(
            week_end_date=week_end_date,
            generated_at=generated_at,
            timezone=timezone,
            argentina_items=argentina_items,
            international_items=international_items,
            market_items=market_items,
            source_index=source_index,
            open_gaps=open_gaps,
            summary_stats=summary_stats,
        )


def to_json(pack: ReportContextPack) -> str:
    """Serialize a ReportContextPack to JSON."""
    return json.dumps(pack.to_dict(), indent=2, ensure_ascii=False)


def to_markdown(pack: ReportContextPack) -> str:
    """Serialize a ReportContextPack to Markdown."""
    lines = [
        "# Weekly Report Context Pack",
        "",
        "## Instructions",
        "- Separar siempre dato, lectura y precio",
        "- Explicar mecanismo antes que narrativa",
        "- Marcar riesgo, invalidador y señal temprana de forma observable",
        "- Declarar confianza según calidad de evidencia",
        "",
        "## Reporting Window",
        f"- Week End Date: {pack.week_end_date}",
        f"- Timezone: {pack.timezone}",
        f"- Generated At: {pack.generated_at}",
        "",
        "## Signal Selection",
        f"- Include Threshold: {pack.summary_stats.get('include_threshold', 2)}",
        f"- Lead Threshold: {pack.summary_stats.get('lead_threshold', 3)}",
        f"- Scenario Break Threshold: {pack.summary_stats.get('scenario_break_threshold', 4)}",
        "",
        "## Summary Stats",
        f"- Total Signals: {pack.summary_stats['total_signals']}",
        f"- Included Signals: {pack.summary_stats['included_signals']}",
        f"- Excluded Signals: {pack.summary_stats['excluded_signals']}",
        f"- Argentina Count: {pack.summary_stats['argentina_count']}",
        f"- International Count: {pack.summary_stats['international_count']}",
        f"- Market Count: {pack.summary_stats['market_count']}",
        f"- Source Count: {pack.summary_stats['source_count']}",
        "",
        "## Sections",
        "",
    ]

    if pack.argentina_items:
        lines.append("### Argentina")
        lines.append("#### Inflación y Actividad")
        for item in pack.argentina_items:
            lines.append(f"- **{item.topic}** (score: {item.score}, confianza: {item.confidence})")
            lines.append(f"  - Dato: {item.fact}")
            lines.append(f"  - Lectura: {item.interpretation}")
            lines.append(f"  - Mecanismo: {item.mechanism}")
            lines.append(f"  - Confirma: {item.confirm_variable}")
            lines.append(f"  - Invalida: {item.invalidate_variable}")
            lines.append(f"  - Fuentes: {', '.join(item.source_ids)}")
            lines.append("")

    if pack.international_items:
        lines.append("### Internacional")
        lines.append("#### Geopolítica")
        for item in pack.international_items:
            lines.append(f"- **{item.topic}** (score: {item.score}, confianza: {item.confidence})")
            lines.append(f"  - Dato: {item.fact}")
            lines.append(f"  - Lectura: {item.interpretation}")
            lines.append(f"  - Mecanismo: {item.mechanism}")
            lines.append(f"  - Confirma: {item.confirm_variable}")
            lines.append(f"  - Invalida: {item.invalidate_variable}")
            lines.append(f"  - Fuentes: {', '.join(item.source_ids)}")
            lines.append("")

    if pack.market_items:
        lines.append("### Mercado")
        lines.append("#### FX")
        for item in pack.market_items:
            lines.append(f"- **{item.topic}** (score: {item.score}, confianza: {item.confidence})")
            lines.append(f"  - Dato: {item.fact}")
            lines.append(f"  - Lectura: {item.interpretation}")
            lines.append(f"  - Mecanismo: {item.mechanism}")
            lines.append(f"  - Confirma: {item.confirm_variable}")
            lines.append(f"  - Invalida: {item.invalidate_variable}")
            lines.append(f"  - Fuentes: {', '.join(item.source_ids)}")
            lines.append("")

    lines.append("## Source Index")
    for entry in pack.source_index:
        lines.append(f"- **{entry.id}**: {entry.label}")
        lines.append(f"  - Type: {entry.type}, Region: {entry.region}")
        lines.append(f"  - URL: {entry.url}")
        lines.append(f"  - Published: {entry.published_at}, Accessed: {entry.accessed_at}")
        lines.append(f"  - Supports: {', '.join(entry.supports)}")
        lines.append(f"  - Confidence Impact: {entry.confidence_impact}")
        lines.append("")

    if pack.open_gaps:
        lines.append("## Open Gaps")
        for gap in pack.open_gaps:
            lines.append(f"- **{gap.section}**: {gap.missing_input}")
            lines.append(f"  - Fallback: {gap.fallback_used or 'None'}")
            lines.append(f"  - Confidence Adjustment: {gap.confidence_adjustment}")
            lines.append(f"  - Note: {gap.note}")
            lines.append("")

    lines.append("## Input Payload (JSON)")
    lines.append("```json")
    lines.append(to_json(pack))
    lines.append("```")

    return "\n".join(lines)