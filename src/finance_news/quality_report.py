"""Quality report module for evaluating connector health and data quality."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Literal


class Severity(str, Enum):
    """Severity levels following the connector quality matrix."""

    S0 = "S0"
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"


class SourceFrequency(str, Enum):
    """Source publication frequency types."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    EVENT = "event"


class FreshnessStatus(str, Enum):
    """Freshness status for connector data."""

    FRESH = "fresh"
    STALE = "stale"
    MISSING = "missing"


@dataclass(frozen=True)
class FreshnessEvaluation:
    """Result of freshness evaluation for a connector."""

    status: FreshnessStatus
    lag_hours: float | None
    threshold_hours: float
    notes: str = ""


@dataclass(frozen=True)
class ConnectorQuality:
    """Quality assessment for a single connector."""

    connector_name: str
    severity: Severity
    freshness_status: FreshnessStatus
    freshness_lag_hours: float | None
    freshness_threshold_hours: float
    completeness: float
    provenance_present: bool
    last_error: str | None
    test_coverage: bool
    source_frequency: SourceFrequency
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "connector_name": self.connector_name,
            "severity": self.severity.value,
            "freshness_status": self.freshness_status.value,
            "freshness_lag_hours": self.freshness_lag_hours,
            "freshness_threshold_hours": self.freshness_threshold_hours,
            "completeness": self.completeness,
            "provenance_present": self.provenance_present,
            "last_error": self.last_error,
            "test_coverage": self.test_coverage,
            "source_frequency": self.source_frequency.value,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConnectorQuality":
        """Create from dictionary representation."""
        return cls(
            connector_name=str(data["connector_name"]),
            severity=Severity(data["severity"]),
            freshness_status=FreshnessStatus(data["freshness_status"]),
            freshness_lag_hours=data.get("freshness_lag_hours"),
            freshness_threshold_hours=float(data["freshness_threshold_hours"]),
            completeness=float(data["completeness"]),
            provenance_present=bool(data["provenance_present"]),
            last_error=data.get("last_error"),
            test_coverage=bool(data["test_coverage"]),
            source_frequency=SourceFrequency(data["source_frequency"]),
            notes=str(data.get("notes", "")),
        )


@dataclass(frozen=True)
class QualityReportSummary:
    """Summary statistics for a quality report."""

    total_connectors: int
    s0_count: int
    s1_count: int
    s2_count: int
    s3_count: int
    fresh_count: int
    stale_count: int
    missing_count: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total_connectors": self.total_connectors,
            "s0_count": self.s0_count,
            "s1_count": self.s1_count,
            "s2_count": self.s2_count,
            "s3_count": self.s3_count,
            "fresh_count": self.fresh_count,
            "stale_count": self.stale_count,
            "missing_count": self.missing_count,
        }


@dataclass(frozen=True)
class QualityReport:
    """Complete quality report for all connectors."""

    generated_at: datetime
    per_connector: list[ConnectorQuality]
    summary: QualityReportSummary

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "generated_at": self.generated_at.isoformat(),
            "per_connector": [item.to_dict() for item in self.per_connector],
            "summary": self.summary.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QualityReport":
        """Create from dictionary representation."""
        return cls(
            generated_at=datetime.fromisoformat(data["generated_at"]),
            per_connector=[
                ConnectorQuality.from_dict(item) for item in data["per_connector"]
            ],
            summary=QualityReportSummary(**data["summary"]),
        )


class QualityReporter:
    """Builds quality reports from connector result data."""

    def __init__(self) -> None:
        """Initialize the quality reporter."""
        self._freshness_thresholds = {
            SourceFrequency.DAILY: {
                "healthy_hours": 6.0,
                "stale_hours": 24.0,
                "critical_hours": 48.0,
            },
            SourceFrequency.WEEKLY: {
                "healthy_hours": 48.0,
                "stale_hours": 168.0,
                "critical_hours": 336.0,
            },
            SourceFrequency.MONTHLY: {
                "healthy_hours": 72.0,
                "stale_hours": 240.0,
                "critical_hours": 1080.0,
            },
            SourceFrequency.EVENT: {
                "healthy_hours": 1.0,
                "stale_hours": 6.0,
                "critical_hours": float("inf"),
            },
        }

    def build_report(self, connector_results: list[dict[str, Any]]) -> QualityReport:
        """Build a quality report from connector result data.

        Args:
            connector_results: List of connector result dictionaries.

        Returns:
            A QualityReport with per-connector assessments and summary.
        """
        per_connector = []
        for result in connector_results:
            quality = self._evaluate_connector(result)
            per_connector.append(quality)

        summary = self._build_summary(per_connector)
        report = QualityReport(
            generated_at=datetime.now(timezone.utc),
            per_connector=per_connector,
            summary=summary,
        )
        return report

    def _evaluate_connector(self, result: dict[str, Any]) -> ConnectorQuality:
        """Evaluate a single connector's quality.

        Args:
            result: Connector result dictionary.

        Returns:
            ConnectorQuality assessment.
        """
        connector_name = result.get("connector_name", "unknown")
        source_frequency = SourceFrequency(result.get("source_frequency", "daily"))

        freshness_eval = self._evaluate_freshness(result, source_frequency)
        severity = self._calculate_severity(result, freshness_eval)

        completeness = float(result.get("completeness", 1.0))
        provenance_present = bool(result.get("provenance_present", True))
        last_error = result.get("last_error")
        test_coverage = bool(result.get("test_coverage", True))
        notes = result.get("notes", "")

        return ConnectorQuality(
            connector_name=connector_name,
            severity=severity,
            freshness_status=freshness_eval.status,
            freshness_lag_hours=freshness_eval.lag_hours,
            freshness_threshold_hours=freshness_eval.threshold_hours,
            completeness=completeness,
            provenance_present=provenance_present,
            last_error=last_error,
            test_coverage=test_coverage,
            source_frequency=source_frequency,
            notes=notes,
        )

    def _evaluate_freshness(
        self, result: dict[str, Any], frequency: SourceFrequency
    ) -> FreshnessEvaluation:
        """Evaluate freshness of connector data.

        Args:
            result: Connector result dictionary.
            frequency: Source publication frequency.

        Returns:
            FreshnessEvaluation with status and lag information.
        """
        published_at = result.get("published_at")
        fetched_at = result.get("fetched_at")
        now = datetime.now(timezone.utc)

        if published_at is None:
            return FreshnessEvaluation(
                status=FreshnessStatus.MISSING,
                lag_hours=None,
                threshold_hours=self._freshness_thresholds[frequency]["healthy_hours"],
                notes="No published_at timestamp available",
            )

        if fetched_at is None:
            fetched_at = now

        published_dt = (
            datetime.fromisoformat(published_at)
            if isinstance(published_at, str)
            else published_at
        )
        fetched_dt = (
            datetime.fromisoformat(fetched_at) if isinstance(fetched_at, str) else fetched_at
        )

        if not isinstance(published_dt, datetime):
            published_dt = now
        if not isinstance(fetched_dt, datetime):
            fetched_dt = now

        lag_hours = (fetched_dt - published_dt).total_seconds() / 3600.0

        thresholds = self._freshness_thresholds[frequency]
        if lag_hours <= thresholds["healthy_hours"]:
            return FreshnessEvaluation(
                status=FreshnessStatus.FRESH,
                lag_hours=lag_hours,
                threshold_hours=thresholds["healthy_hours"],
                notes=f"Data is fresh (lag: {lag_hours:.1f}h)",
            )
        elif lag_hours <= thresholds["stale_hours"]:
            return FreshnessEvaluation(
                status=FreshnessStatus.STALE,
                lag_hours=lag_hours,
                threshold_hours=thresholds["healthy_hours"],
                notes=f"Data is stale (lag: {lag_hours:.1f}h)",
            )
        else:
            return FreshnessEvaluation(
                status=FreshnessStatus.STALE,
                lag_hours=lag_hours,
                threshold_hours=thresholds["healthy_hours"],
                notes=f"Data is critically stale (lag: {lag_hours:.1f}h)",
            )

    def _calculate_severity(
        self, result: dict[str, Any], freshness_eval: FreshnessEvaluation
    ) -> Severity:
        """Calculate severity level based on connector metrics.

        Args:
            result: Connector result dictionary.
            freshness_eval: Freshness evaluation result.

        Returns:
            Severity level (S0, S1, S2, or S3).
        """
        severity_scores = []

        provenance_present = result.get("provenance_present", True)
        if not provenance_present:
            return Severity.S0

        completeness = result.get("completeness", 1.0)
        if completeness < 0.5:
            severity_scores.append((Severity.S0, 0))
        elif completeness < 0.8:
            severity_scores.append((Severity.S2, 1))

        last_error = result.get("last_error")
        if last_error:
            error_type = str(last_error)
            if "timeout" in error_type.lower() or "network" in error_type.lower():
                severity_scores.append((Severity.S1, 0))
            elif "parse" in error_type.lower() or "validation" in error_type.lower():
                severity_scores.append((Severity.S2, 1))
            else:
                severity_scores.append((Severity.S3, 2))

        test_coverage = result.get("test_coverage", True)
        if not test_coverage:
            severity_scores.append((Severity.S2, 1))

        if freshness_eval.status == FreshnessStatus.STALE:
            source_frequency = SourceFrequency(result.get("source_frequency", "daily"))
            thresholds = self._freshness_thresholds[source_frequency]
            if freshness_eval.lag_hours is not None:
                if freshness_eval.lag_hours > thresholds["critical_hours"]:
                    severity_scores.append((Severity.S1, 0))
                else:
                    severity_scores.append((Severity.S2, 1))

        if not severity_scores:
            return Severity.S0

        severity_scores.sort(key=lambda x: x[1])
        return severity_scores[0][0]

    def _build_summary(self, per_connector: list[ConnectorQuality]) -> QualityReportSummary:
        """Build summary statistics from connector quality assessments.

        Args:
            per_connector: List of connector quality assessments.

        Returns:
            QualityReportSummary with counts by severity and freshness.
        """
        s0_count = sum(1 for c in per_connector if c.severity == Severity.S0)
        s1_count = sum(1 for c in per_connector if c.severity == Severity.S1)
        s2_count = sum(1 for c in per_connector if c.severity == Severity.S2)
        s3_count = sum(1 for c in per_connector if c.severity == Severity.S3)

        fresh_count = sum(1 for c in per_connector if c.freshness_status == FreshnessStatus.FRESH)
        stale_count = sum(1 for c in per_connector if c.freshness_status == FreshnessStatus.STALE)
        missing_count = sum(1 for c in per_connector if c.freshness_status == FreshnessStatus.MISSING)

        return QualityReportSummary(
            total_connectors=len(per_connector),
            s0_count=s0_count,
            s1_count=s1_count,
            s2_count=s2_count,
            s3_count=s3_count,
            fresh_count=fresh_count,
            stale_count=stale_count,
            missing_count=missing_count,
        )