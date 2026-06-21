from __future__ import annotations

from finance_news.context_pack import (
    ContextPackItem,
    OpenGap,
    ReportContextPack,
    SourceIndexEntry,
)


class MarkdownReportGenerator:
    """Deterministic Markdown generator for weekly reports from ReportContextPack."""

    def generate(self, pack: ReportContextPack) -> str:
        """Generate a complete Markdown weekly report from a context pack.

        Args:
            pack: The report context pack with all items, sources, and gaps.

        Returns:
            A complete Markdown report string.
        """
        lines: list[str] = []

        # Header
        lines.extend(self._generate_header(pack))
        lines.append("")

        # Sections in the specified order
        lines.extend(self._generate_argentina_section(pack))
        lines.append("")

        lines.extend(self._generate_international_section(pack))
        lines.append("")

        lines.extend(self._generate_market_section(pack))
        lines.append("")

        lines.extend(self._generate_scenarios_section(pack))
        lines.append("")

        lines.extend(self._generate_risks_section(pack))
        lines.append("")

        lines.extend(self._generate_watch_list_section(pack))
        lines.append("")

        # Source index appendix
        lines.extend(self._generate_source_index(pack))
        lines.append("")

        return "\n".join(lines)

    def _generate_header(self, pack: ReportContextPack) -> list[str]:
        """Generate the report header."""
        return [
            "# Reporte Semanal",
            "",
            f"**Semana finaliza:** {pack.week_end_date}",
            f"**Zona horaria:** {pack.timezone}",
            f"**Generado:** {pack.generated_at}",
            "",
            f"**Estadísticas:** {pack.summary_stats['total_signals']} señales totales, "
            f"{pack.summary_stats['included_signals']} incluidas, "
            f"{pack.summary_stats['source_count']} fuentes",
        ]

    def _generate_argentina_section(self, pack: ReportContextPack) -> list[str]:
        """Generate the Argentina section."""
        lines = [
            "## Argentina",
            "",
        ]

        if not pack.argentina_items:
            lines.append("*Sin datos para esta semana.*")
            return lines

        lines.append("### Inflación y Actividad")
        lines.append("")

        for item in sorted(pack.argentina_items, key=lambda i: (i.topic, i.score)):
            lines.extend(self._format_item(item))

        return lines

    def _generate_international_section(self, pack: ReportContextPack) -> list[str]:
        """Generate the Internacional section."""
        lines = [
            "## Internacional",
            "",
        ]

        if not pack.international_items:
            lines.append("*Sin datos para esta semana.*")
            return lines

        lines.append("### Geopolítica")
        lines.append("")

        for item in sorted(pack.international_items, key=lambda i: (i.topic, i.score)):
            lines.extend(self._format_item(item))

        return lines

    def _generate_market_section(self, pack: ReportContextPack) -> list[str]:
        """Generate the Mercado section."""
        lines = [
            "## Mercado",
            "",
        ]

        if not pack.market_items:
            lines.append("*Sin datos para esta semana.*")
            return lines

        lines.append("### FX")
        lines.append("")

        for item in sorted(pack.market_items, key=lambda i: (i.topic, i.score)):
            lines.extend(self._format_item(item))

        return lines

    def _generate_scenarios_section(self, pack: ReportContextPack) -> list[str]:
        """Generate the Escenarios section."""
        lines = [
            "## Escenarios",
            "",
        ]

        if not pack.argentina_items and not pack.international_items:
            lines.append("*Sin datos para análisis de escenarios.*")
            return lines

        lines.append("### Escenario Base")
        lines.append("")
        lines.append("**Disparadores:**")
        lines.append("- Estabilización de las variables principales observadas.")
        lines.append("")

        lines.append("**Mecanismo:**")
        lines.append("- Los datos de inflación y actividad se mantienen en rangos esperados.")
        lines.append("- No hay rupturas en el mercado cambiario ni de tasas.")
        lines.append("")

        lines.append("**Activos más sensibles:**")
        lines.append("- Bonos soberanos en pesos y dólares.")
        lines.append("- Tipo de cambio paralelo (MEP/CCL).")
        lines.append("")

        lines.append("**Probabilidad cualitativa:** Media")
        lines.append("")

        lines.append("**Hito que lo valida:**")
        lines.append("- Estabilidad en precios de mercado por 2 semanas consecutivas.")
        lines.append("")

        lines.append("**Hito que lo descarta:**")
        lines.append("- Salto discreto en tipo de cambio o tasas > 15%.")
        lines.append("")

        lines.append("### Escenario Positivo")
        lines.append("")
        lines.append("**Disparadores:**")
        lines.append("- Mejora en indicadores de actividad menor a la esperada.")
        lines.append("")

        lines.append("**Mecanismo:**")
        lines.append("- Recuperación más rápida de la economía.")
        lines.append("- Mayor liquidez y menor presión cambiaria.")
        lines.append("")

        lines.append("**Activos más sensibles:**")
        lines.append("- Acciones locales.")
        lines.append("- Riesgo país.")
        lines.append("")

        lines.append("**Probabilidad cualitativa:** Baja")
        lines.append("")

        lines.append("**Hito que lo valida:**")
        lines.append("- Serie de datos positivos consecutivos.")
        lines.append("")

        lines.append("**Hito que lo descarta:**")
        lines.append("- Deterioro de reservas o brecha cambiaria.")
        lines.append("")

        lines.append("### Escenario Negativo")
        lines.append("")
        lines.append("**Disparadores:**")
        lines.append("- Aceleración de inflación o devaluación.")
        lines.append("")

        lines.append("**Mecanismo:**")
        lines.append("- Pérdida de reservas y presión sobre el tipo de cambio.")
        lines.append("- Ajuste monetario más agresivo.")
        lines.append("")

        lines.append("**Activos más sensibles:**")
        lines.append("- Dólar oficial y paralelo.")
        lines.append("- Tasa Badlar y pases.")
        lines.append("")

        lines.append("**Probabilidad cualitativa:** Media")
        lines.append("")

        lines.append("**Hito que lo valida:**")
        lines.append("- Salto en tipo de cambio o pérdida de reservas > USD 1B/semana.")
        lines.append("")

        lines.append("**Hito que lo descarta:**")
        lines.append("- Estabilidad de reservas por 3 semanas.")
        lines.append("")

        return lines

    def _generate_risks_section(self, pack: ReportContextPack) -> list[str]:
        """Generate the Riesgos section."""
        lines = [
            "## Riesgos que rompen el escenario",
            "",
        ]

        if not pack.open_gaps:
            lines.append("*Sin riesgos identificados esta semana.*")
            return lines

        lines.append("### Riesgos Observables")
        lines.append("")

        # Derive risks from open gaps and low-confidence items
        all_items = pack.argentina_items + pack.international_items + pack.market_items
        low_confidence_items = [
            item for item in all_items if item.confidence == "baja"
        ]

        if low_confidence_items:
            for item in sorted(low_confidence_items, key=lambda i: (i.topic, i.score)):
                lines.append(f"**Riesgo:** {item.topic}")
                lines.append(f"- **Tipo:** Mercado")
                lines.append(f"- **Canal de transmisión:** {item.mechanism}")
                lines.append(f"- **Señal temprana:** {item.confirm_variable}")
                lines.append(f"- **Impacto probable:** {item.invalidate_variable}")
                lines.append(f"- **Confianza:** {item.confidence}")
                if item.source_ids:
                    lines.append(f"- **Fuente:** {self._format_sources(item.source_ids, pack.source_index)}")
                lines.append("")

        if pack.open_gaps:
            lines.append("### Gaps de Información")
            lines.append("")
            for gap in sorted(pack.open_gaps, key=lambda g: g.section):
                lines.append(f"**Sección:** {gap.section}")
                lines.append(f"- **Faltante:** {gap.missing_input}")
                if gap.fallback_used:
                    lines.append(f"- **Fallback:** {gap.fallback_used}")
                lines.append(f"- **Ajuste de confianza:** {gap.confidence_adjustment}")
                lines.append(f"- **Nota:** {gap.note}")
                lines.append("")

        return lines

    def _generate_watch_list_section(self, pack: ReportContextPack) -> list[str]:
        """Generate the Qué mirar section."""
        lines = [
            "## Qué mirar la semana próxima",
            "",
        ]

        if not pack.argentina_items and not pack.international_items:
            lines.append("*Sin eventos clave identificados.*")
            return lines

        lines.append("### Eventos y Datos a Monitorear")
        lines.append("")

        all_items = pack.argentina_items + pack.international_items + pack.market_items

        for item in sorted(all_items, key=lambda i: (i.topic, i.score)):
            lines.append(f"**Evento/dato:** {item.topic}")
            lines.append(f"- **Fecha esperada:** Próxima semana (a confirmar)")
            lines.append(f"- **Por qué importa:** {item.interpretation}")
            lines.append(f"- **Resultado positivo:** {item.confirm_variable}")
            lines.append(f"- **Resultado negativo:** {item.invalidate_variable}")
            lines.append(f"- **Mercado/variable a mirar:** {item.mechanism}")
            if item.source_ids:
                lines.append(f"- **Fuente:** {self._format_sources(item.source_ids, pack.source_index)}")
            lines.append("")

        return lines

    def _generate_source_index(self, pack: ReportContextPack) -> list[str]:
        """Generate the source index appendix."""
        lines = [
            "## Índice de Fuentes",
            "",
        ]

        if not pack.source_index:
            lines.append("*Sin fuentes indexadas.*")
            return lines

        for entry in sorted(pack.source_index, key=lambda e: e.id):
            lines.append(f"**{entry.id}**: {entry.label}")
            if entry.url:
                lines.append(f"- URL: {entry.url}")
            lines.append(f"- Tipo: {entry.type}, Región: {entry.region}")
            if entry.published_at:
                lines.append(f"- Publicado: {entry.published_at}")
            lines.append(f"- Accedido: {entry.accessed_at}")
            if entry.supports:
                lines.append(f"- Soporta: {', '.join(sorted(entry.supports))}")
            if entry.confidence_impact != "none":
                lines.append(f"- Impacto en confianza: {entry.confidence_impact}")
            lines.append("")

        return lines

    def _format_item(self, item: ContextPackItem) -> list[str]:
        """Format a single context pack item as Markdown."""
        lines = [
            f"**{item.topic}** (score: {item.score}, confianza: {item.confidence})",
            "",
            f"- **Dato:** {item.fact}",
            f"- **Lectura:** {item.interpretation}",
            f"- **Mecanismo:** {item.mechanism}",
            f"- **Confirma:** {item.confirm_variable}",
            f"- **Invalida:** {item.invalidate_variable}",
        ]

        if item.source_ids:
            lines.append(f"- **Fuente(s):** {self._format_sources(item.source_ids, [])}")

        if item.excerpt:
            lines.append(f"- **Extracto:** {item.excerpt[:100]}")

        lines.append("")
        return lines

    def _format_sources(
        self,
        source_ids: list[str],
        source_index: list[SourceIndexEntry],
    ) -> str:
        """Format source IDs with optional URLs from the index."""
        if not source_ids:
            return "*Sin fuentes*"

        source_map = {entry.id: entry for entry in source_index}
        formatted = []

        for source_id in sorted(source_ids):
            entry = source_map.get(source_id)
            if entry and entry.url:
                formatted.append(f"[{entry.label}]({entry.url})")
            elif entry:
                formatted.append(entry.label)
            else:
                formatted.append(source_id)

        return ", ".join(formatted)


def generate_report(pack: ReportContextPack) -> str:
    """Generate a Markdown weekly report from a context pack.

    This is a convenience function that creates a MarkdownReportGenerator
    and calls generate() on it.

    Args:
        pack: The report context pack.

    Returns:
        The generated Markdown report.
    """
    generator = MarkdownReportGenerator()
    return generator.generate(pack)