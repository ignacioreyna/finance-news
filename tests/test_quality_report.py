"""Tests for quality_report module."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "src")

from finance_news.quality_report import (
    ConnectorQuality,
    FreshnessEvaluation,
    FreshnessStatus,
    QualityReport,
    QualityReportSummary,
    QualityReporter,
    Severity,
    SourceFrequency,
)


class TestFreshnessEvaluation(unittest.TestCase):
    """Test freshness evaluation logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.reporter = QualityReporter()

    def test_freshness_daily_within_threshold(self):
        """Test daily source within healthy threshold."""
        now = datetime.now(timezone.utc)
        result = {
            "connector_name": "test_daily",
            "source_frequency": "daily",
            "published_at": (now - timedelta(hours=4)).isoformat(),
            "fetched_at": now.isoformat(),
        }
        eval_result = self.reporter._evaluate_freshness(
            result, SourceFrequency.DAILY
        )
        self.assertEqual(eval_result.status, FreshnessStatus.FRESH)
        self.assertAlmostEqual(eval_result.lag_hours, 4.0, delta=0.1)
        self.assertEqual(eval_result.threshold_hours, 6.0)

    def test_freshness_daily_stale(self):
        """Test daily source beyond healthy threshold."""
        now = datetime.now(timezone.utc)
        result = {
            "connector_name": "test_daily",
            "source_frequency": "daily",
            "published_at": (now - timedelta(hours=12)).isoformat(),
            "fetched_at": now.isoformat(),
        }
        eval_result = self.reporter._evaluate_freshness(
            result, SourceFrequency.DAILY
        )
        self.assertEqual(eval_result.status, FreshnessStatus.STALE)
        self.assertAlmostEqual(eval_result.lag_hours, 12.0, delta=0.1)

    def test_freshness_daily_critical(self):
        """Test daily source beyond critical threshold."""
        now = datetime.now(timezone.utc)
        result = {
            "connector_name": "test_daily",
            "source_frequency": "daily",
            "published_at": (now - timedelta(hours=30)).isoformat(),
            "fetched_at": now.isoformat(),
        }
        eval_result = self.reporter._evaluate_freshness(
            result, SourceFrequency.DAILY
        )
        self.assertEqual(eval_result.status, FreshnessStatus.STALE)
        self.assertAlmostEqual(eval_result.lag_hours, 30.0, delta=0.1)

    def test_freshness_weekly_within_threshold(self):
        """Test weekly source within healthy threshold."""
        now = datetime.now(timezone.utc)
        result = {
            "connector_name": "test_weekly",
            "source_frequency": "weekly",
            "published_at": (now - timedelta(hours=24)).isoformat(),
            "fetched_at": now.isoformat(),
        }
        eval_result = self.reporter._evaluate_freshness(
            result, SourceFrequency.WEEKLY
        )
        self.assertEqual(eval_result.status, FreshnessStatus.FRESH)
        self.assertAlmostEqual(eval_result.lag_hours, 24.0, delta=0.1)

    def test_freshness_weekly_stale(self):
        """Test weekly source beyond healthy threshold."""
        now = datetime.now(timezone.utc)
        result = {
            "connector_name": "test_weekly",
            "source_frequency": "weekly",
            "published_at": (now - timedelta(hours=96)).isoformat(),
            "fetched_at": now.isoformat(),
        }
        eval_result = self.reporter._evaluate_freshness(
            result, SourceFrequency.WEEKLY
        )
        self.assertEqual(eval_result.status, FreshnessStatus.STALE)
        self.assertAlmostEqual(eval_result.lag_hours, 96.0, delta=0.1)

    def test_freshness_monthly_within_threshold(self):
        """Test monthly source within healthy threshold."""
        now = datetime.now(timezone.utc)
        result = {
            "connector_name": "test_monthly",
            "source_frequency": "monthly",
            "published_at": (now - timedelta(hours=48)).isoformat(),
            "fetched_at": now.isoformat(),
        }
        eval_result = self.reporter._evaluate_freshness(
            result, SourceFrequency.MONTHLY
        )
        self.assertEqual(eval_result.status, FreshnessStatus.FRESH)
        self.assertAlmostEqual(eval_result.lag_hours, 48.0, delta=0.1)

    def test_freshness_monthly_stale(self):
        """Test monthly source beyond healthy threshold."""
        now = datetime.now(timezone.utc)
        result = {
            "connector_name": "test_monthly",
            "source_frequency": "monthly",
            "published_at": (now - timedelta(hours=120)).isoformat(),
            "fetched_at": now.isoformat(),
        }
        eval_result = self.reporter._evaluate_freshness(
            result, SourceFrequency.MONTHLY
        )
        self.assertEqual(eval_result.status, FreshnessStatus.STALE)
        self.assertAlmostEqual(eval_result.lag_hours, 120.0, delta=0.1)

    def test_freshness_event_within_threshold(self):
        """Test event source within healthy threshold."""
        now = datetime.now(timezone.utc)
        result = {
            "connector_name": "test_event",
            "source_frequency": "event",
            "published_at": (now - timedelta(minutes=30)).isoformat(),
            "fetched_at": now.isoformat(),
        }
        eval_result = self.reporter._evaluate_freshness(
            result, SourceFrequency.EVENT
        )
        self.assertEqual(eval_result.status, FreshnessStatus.FRESH)
        self.assertAlmostEqual(eval_result.lag_hours, 0.5, delta=0.1)

    def test_freshness_event_stale(self):
        """Test event source beyond healthy threshold."""
        now = datetime.now(timezone.utc)
        result = {
            "connector_name": "test_event",
            "source_frequency": "event",
            "published_at": (now - timedelta(hours=3)).isoformat(),
            "fetched_at": now.isoformat(),
        }
        eval_result = self.reporter._evaluate_freshness(
            result, SourceFrequency.EVENT
        )
        self.assertEqual(eval_result.status, FreshnessStatus.STALE)
        self.assertAlmostEqual(eval_result.lag_hours, 3.0, delta=0.1)

    def test_freshness_missing_timestamp(self):
        """Test handling of missing published_at timestamp."""
        result = {
            "connector_name": "test_missing",
            "source_frequency": "daily",
        }
        eval_result = self.reporter._evaluate_freshness(
            result, SourceFrequency.DAILY
        )
        self.assertEqual(eval_result.status, FreshnessStatus.MISSING)
        self.assertIsNone(eval_result.lag_hours)


class TestSeverityCalculation(unittest.TestCase):
    """Test severity level calculation."""

    def setUp(self):
        """Set up test fixtures."""
        self.reporter = QualityReporter()
        self.now = datetime.now(timezone.utc)

    def test_severity_s0_perfect(self):
        """Test S0 severity for perfect connector."""
        result = {
            "connector_name": "perfect_connector",
            "source_frequency": "daily",
            "published_at": (self.now - timedelta(hours=2)).isoformat(),
            "fetched_at": self.now.isoformat(),
            "provenance_present": True,
            "completeness": 1.0,
            "last_error": None,
            "test_coverage": True,
        }
        freshness_eval = self.reporter._evaluate_freshness(result, SourceFrequency.DAILY)
        severity = self.reporter._calculate_severity(result, freshness_eval)
        self.assertEqual(severity, Severity.S0)

    def test_severity_s0_no_provenance(self):
        """Test S0 severity for missing provenance (blocking)."""
        result = {
            "connector_name": "no_provenance",
            "source_frequency": "daily",
            "published_at": (self.now - timedelta(hours=2)).isoformat(),
            "fetched_at": self.now.isoformat(),
            "provenance_present": False,
            "completeness": 1.0,
            "last_error": None,
            "test_coverage": True,
        }
        freshness_eval = self.reporter._evaluate_freshness(result, SourceFrequency.DAILY)
        severity = self.reporter._calculate_severity(result, freshness_eval)
        self.assertEqual(severity, Severity.S0)

    def test_severity_s0_low_completeness(self):
        """Test S0 severity for very low completeness."""
        result = {
            "connector_name": "low_completeness",
            "source_frequency": "daily",
            "published_at": (self.now - timedelta(hours=2)).isoformat(),
            "fetched_at": self.now.isoformat(),
            "provenance_present": True,
            "completeness": 0.3,
            "last_error": None,
            "test_coverage": True,
        }
        freshness_eval = self.reporter._evaluate_freshness(result, SourceFrequency.DAILY)
        severity = self.reporter._calculate_severity(result, freshness_eval)
        self.assertEqual(severity, Severity.S0)

    def test_severity_s1_network_error(self):
        """Test S1 severity for network/timeout errors."""
        result = {
            "connector_name": "network_error",
            "source_frequency": "daily",
            "published_at": (self.now - timedelta(hours=2)).isoformat(),
            "fetched_at": self.now.isoformat(),
            "provenance_present": True,
            "completeness": 1.0,
            "last_error": "TimeoutError: Connection timed out",
            "test_coverage": True,
        }
        freshness_eval = self.reporter._evaluate_freshness(result, SourceFrequency.DAILY)
        severity = self.reporter._calculate_severity(result, freshness_eval)
        self.assertEqual(severity, Severity.S1)

    def test_severity_s1_critical_stale_daily(self):
        """Test S1 severity for critically stale daily source."""
        result = {
            "connector_name": "stale_daily",
            "source_frequency": "daily",
            "published_at": (self.now - timedelta(hours=50)).isoformat(),
            "fetched_at": self.now.isoformat(),
            "provenance_present": True,
            "completeness": 1.0,
            "last_error": None,
            "test_coverage": True,
        }
        freshness_eval = self.reporter._evaluate_freshness(result, SourceFrequency.DAILY)
        severity = self.reporter._calculate_severity(result, freshness_eval)
        self.assertEqual(severity, Severity.S1)

    def test_severity_s2_moderate_completeness(self):
        """Test S2 severity for moderate completeness issues."""
        result = {
            "connector_name": "moderate_completeness",
            "source_frequency": "daily",
            "published_at": (self.now - timedelta(hours=2)).isoformat(),
            "fetched_at": self.now.isoformat(),
            "provenance_present": True,
            "completeness": 0.7,
            "last_error": None,
            "test_coverage": True,
        }
        freshness_eval = self.reporter._evaluate_freshness(result, SourceFrequency.DAILY)
        severity = self.reporter._calculate_severity(result, freshness_eval)
        self.assertEqual(severity, Severity.S2)

    def test_severity_s2_parse_error(self):
        """Test S2 severity for parse/validation errors."""
        result = {
            "connector_name": "parse_error",
            "source_frequency": "daily",
            "published_at": (self.now - timedelta(hours=2)).isoformat(),
            "fetched_at": self.now.isoformat(),
            "provenance_present": True,
            "completeness": 1.0,
            "last_error": "ValidationError: Missing required field",
            "test_coverage": True,
        }
        freshness_eval = self.reporter._evaluate_freshness(result, SourceFrequency.DAILY)
        severity = self.reporter._calculate_severity(result, freshness_eval)
        self.assertEqual(severity, Severity.S2)

    def test_severity_s2_no_test_coverage(self):
        """Test S2 severity for missing test coverage."""
        result = {
            "connector_name": "no_tests",
            "source_frequency": "daily",
            "published_at": (self.now - timedelta(hours=2)).isoformat(),
            "fetched_at": self.now.isoformat(),
            "provenance_present": True,
            "completeness": 1.0,
            "last_error": None,
            "test_coverage": False,
        }
        freshness_eval = self.reporter._evaluate_freshness(result, SourceFrequency.DAILY)
        severity = self.reporter._calculate_severity(result, freshness_eval)
        self.assertEqual(severity, Severity.S2)

    def test_severity_s2_moderate_stale(self):
        """Test S2 severity for moderately stale data."""
        result = {
            "connector_name": "moderate_stale",
            "source_frequency": "daily",
            "published_at": (self.now - timedelta(hours=12)).isoformat(),
            "fetched_at": self.now.isoformat(),
            "provenance_present": True,
            "completeness": 1.0,
            "last_error": None,
            "test_coverage": True,
        }
        freshness_eval = self.reporter._evaluate_freshness(result, SourceFrequency.DAILY)
        severity = self.reporter._calculate_severity(result, freshness_eval)
        self.assertEqual(severity, Severity.S2)

    def test_severity_s3_other_error(self):
        """Test S3 severity for other non-critical errors."""
        result = {
            "connector_name": "other_error",
            "source_frequency": "daily",
            "published_at": (self.now - timedelta(hours=2)).isoformat(),
            "fetched_at": self.now.isoformat(),
            "provenance_present": True,
            "completeness": 1.0,
            "last_error": "Warning: Deprecated field used",
            "test_coverage": True,
        }
        freshness_eval = self.reporter._evaluate_freshness(result, SourceFrequency.DAILY)
        severity = self.reporter._calculate_severity(result, freshness_eval)
        self.assertEqual(severity, Severity.S3)


class TestConnectorQuality(unittest.TestCase):
    """Test ConnectorQuality dataclass."""

    def test_connector_quality_creation(self):
        """Test creating ConnectorQuality instance."""
        now = datetime.now(timezone.utc)
        quality = ConnectorQuality(
            connector_name="test_connector",
            severity=Severity.S0,
            freshness_status=FreshnessStatus.FRESH,
            freshness_lag_hours=2.5,
            freshness_threshold_hours=6.0,
            completeness=1.0,
            provenance_present=True,
            last_error=None,
            test_coverage=True,
            source_frequency=SourceFrequency.DAILY,
            notes="Test connector",
        )
        self.assertEqual(quality.connector_name, "test_connector")
        self.assertEqual(quality.severity, Severity.S0)
        self.assertEqual(quality.freshness_status, FreshnessStatus.FRESH)
        self.assertAlmostEqual(quality.freshness_lag_hours, 2.5)

    def test_connector_quality_to_dict(self):
        """Test ConnectorQuality serialization to dict."""
        quality = ConnectorQuality(
            connector_name="test_connector",
            severity=Severity.S0,
            freshness_status=FreshnessStatus.FRESH,
            freshness_lag_hours=2.5,
            freshness_threshold_hours=6.0,
            completeness=1.0,
            provenance_present=True,
            last_error=None,
            test_coverage=True,
            source_frequency=SourceFrequency.DAILY,
        )
        data = quality.to_dict()
        self.assertEqual(data["connector_name"], "test_connector")
        self.assertEqual(data["severity"], "S0")
        self.assertEqual(data["freshness_status"], "fresh")
        self.assertEqual(data["source_frequency"], "daily")

    def test_connector_quality_from_dict(self):
        """Test ConnectorQuality deserialization from dict."""
        data = {
            "connector_name": "test_connector",
            "severity": "S0",
            "freshness_status": "fresh",
            "freshness_lag_hours": 2.5,
            "freshness_threshold_hours": 6.0,
            "completeness": 1.0,
            "provenance_present": True,
            "last_error": None,
            "test_coverage": True,
            "source_frequency": "daily",
            "notes": "Test",
        }
        quality = ConnectorQuality.from_dict(data)
        self.assertEqual(quality.connector_name, "test_connector")
        self.assertEqual(quality.severity, Severity.S0)
        self.assertEqual(quality.freshness_status, FreshnessStatus.FRESH)


class TestQualityReport(unittest.TestCase):
    """Test QualityReport dataclass."""

    def test_quality_report_creation(self):
        """Test creating QualityReport instance."""
        now = datetime.now(timezone.utc)
        connector_quality = ConnectorQuality(
            connector_name="test_connector",
            severity=Severity.S0,
            freshness_status=FreshnessStatus.FRESH,
            freshness_lag_hours=2.5,
            freshness_threshold_hours=6.0,
            completeness=1.0,
            provenance_present=True,
            last_error=None,
            test_coverage=True,
            source_frequency=SourceFrequency.DAILY,
        )
        summary = QualityReportSummary(
            total_connectors=1,
            s0_count=1,
            s1_count=0,
            s2_count=0,
            s3_count=0,
            fresh_count=1,
            stale_count=0,
            missing_count=0,
        )
        report = QualityReport(
            generated_at=now,
            per_connector=[connector_quality],
            summary=summary,
        )
        self.assertEqual(len(report.per_connector), 1)
        self.assertEqual(report.summary.total_connectors, 1)

    def test_quality_report_to_dict(self):
        """Test QualityReport serialization to dict."""
        now = datetime.now(timezone.utc)
        connector_quality = ConnectorQuality(
            connector_name="test_connector",
            severity=Severity.S0,
            freshness_status=FreshnessStatus.FRESH,
            freshness_lag_hours=2.5,
            freshness_threshold_hours=6.0,
            completeness=1.0,
            provenance_present=True,
            last_error=None,
            test_coverage=True,
            source_frequency=SourceFrequency.DAILY,
        )
        summary = QualityReportSummary(
            total_connectors=1,
            s0_count=1,
            s1_count=0,
            s2_count=0,
            s3_count=0,
            fresh_count=1,
            stale_count=0,
            missing_count=0,
        )
        report = QualityReport(
            generated_at=now,
            per_connector=[connector_quality],
            summary=summary,
        )
        data = report.to_dict()
        self.assertIn("generated_at", data)
        self.assertIn("per_connector", data)
        self.assertIn("summary", data)

    def test_quality_report_from_dict(self):
        """Test QualityReport deserialization from dict."""
        now = datetime.now(timezone.utc)
        data = {
            "generated_at": now.isoformat(),
            "per_connector": [
                {
                    "connector_name": "test_connector",
                    "severity": "S0",
                    "freshness_status": "fresh",
                    "freshness_lag_hours": 2.5,
                    "freshness_threshold_hours": 6.0,
                    "completeness": 1.0,
                    "provenance_present": True,
                    "last_error": None,
                    "test_coverage": True,
                    "source_frequency": "daily",
                    "notes": "",
                }
            ],
            "summary": {
                "total_connectors": 1,
                "s0_count": 1,
                "s1_count": 0,
                "s2_count": 0,
                "s3_count": 0,
                "fresh_count": 1,
                "stale_count": 0,
                "missing_count": 0,
            },
        }
        report = QualityReport.from_dict(data)
        self.assertEqual(len(report.per_connector), 1)
        self.assertEqual(report.summary.total_connectors, 1)


class TestQualityReporterIntegration(unittest.TestCase):
    """Integration tests for QualityReporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.reporter = QualityReporter()
        self.now = datetime.now(timezone.utc)

    def test_build_report_single_connector(self):
        """Test building report with single connector."""
        results = [
            {
                "connector_name": "test_connector",
                "source_frequency": "daily",
                "published_at": (self.now - timedelta(hours=2)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            }
        ]
        report = self.reporter.build_report(results)
        self.assertEqual(len(report.per_connector), 1)
        self.assertEqual(report.summary.total_connectors, 1)
        self.assertEqual(report.summary.s0_count, 1)
        self.assertEqual(report.per_connector[0].connector_name, "test_connector")

    def test_build_report_multiple_connectors(self):
        """Test building report with multiple connectors."""
        results = [
            {
                "connector_name": "connector_1",
                "source_frequency": "daily",
                "published_at": (self.now - timedelta(hours=2)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            },
            {
                "connector_name": "connector_2",
                "source_frequency": "weekly",
                "published_at": (self.now - timedelta(hours=24)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            },
        ]
        report = self.reporter.build_report(results)
        self.assertEqual(len(report.per_connector), 2)
        self.assertEqual(report.summary.total_connectors, 2)

    def test_build_report_mixed_severities(self):
        """Test building report with connectors of different severities."""
        results = [
            {
                "connector_name": "perfect_connector",
                "source_frequency": "daily",
                "published_at": (self.now - timedelta(hours=2)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            },
            {
                "connector_name": "stale_connector",
                "source_frequency": "daily",
                "published_at": (self.now - timedelta(hours=12)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            },
            {
                "connector_name": "error_connector",
                "source_frequency": "daily",
                "published_at": (self.now - timedelta(hours=2)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": "TimeoutError: Connection failed",
                "test_coverage": True,
            },
        ]
        report = self.reporter.build_report(results)
        self.assertEqual(report.summary.total_connectors, 3)
        self.assertEqual(report.summary.s0_count, 1)
        self.assertEqual(report.summary.s1_count, 1)
        self.assertEqual(report.summary.s2_count, 1)

    def test_build_report_all_frequency_types(self):
        """Test building report with all frequency types."""
        results = [
            {
                "connector_name": "daily_connector",
                "source_frequency": "daily",
                "published_at": (self.now - timedelta(hours=2)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            },
            {
                "connector_name": "weekly_connector",
                "source_frequency": "weekly",
                "published_at": (self.now - timedelta(hours=24)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            },
            {
                "connector_name": "monthly_connector",
                "source_frequency": "monthly",
                "published_at": (self.now - timedelta(hours=48)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            },
            {
                "connector_name": "event_connector",
                "source_frequency": "event",
                "published_at": (self.now - timedelta(minutes=30)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            },
        ]
        report = self.reporter.build_report(results)
        self.assertEqual(len(report.per_connector), 4)
        for connector in report.per_connector:
            self.assertEqual(connector.severity, Severity.S0)
            self.assertEqual(connector.freshness_status, FreshnessStatus.FRESH)

    def test_build_report_provenance_presence(self):
        """Test provenance presence detection."""
        results_with_provenance = [
            {
                "connector_name": "with_provenance",
                "source_frequency": "daily",
                "published_at": (self.now - timedelta(hours=2)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            }
        ]
        results_without_provenance = [
            {
                "connector_name": "without_provenance",
                "source_frequency": "daily",
                "published_at": (self.now - timedelta(hours=2)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": False,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            }
        ]
        report_with = self.reporter.build_report(results_with_provenance)
        report_without = self.reporter.build_report(results_without_provenance)
        self.assertTrue(report_with.per_connector[0].provenance_present)
        self.assertFalse(report_without.per_connector[0].provenance_present)
        self.assertEqual(report_without.per_connector[0].severity, Severity.S0)

    def test_build_report_summary_aggregation(self):
        """Test summary aggregation correctly counts all metrics."""
        results = [
            {
                "connector_name": "fresh_connector",
                "source_frequency": "daily",
                "published_at": (self.now - timedelta(hours=2)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            },
            {
                "connector_name": "stale_connector",
                "source_frequency": "daily",
                "published_at": (self.now - timedelta(hours=12)).isoformat(),
                "fetched_at": self.now.isoformat(),
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            },
            {
                "connector_name": "missing_connector",
                "source_frequency": "daily",
                "provenance_present": True,
                "completeness": 1.0,
                "last_error": None,
                "test_coverage": True,
            },
        ]
        report = self.reporter.build_report(results)
        self.assertEqual(report.summary.fresh_count, 1)
        self.assertEqual(report.summary.stale_count, 1)
        self.assertEqual(report.summary.missing_count, 1)

    def test_build_report_empty_results(self):
        """Test building report with empty results."""
        report = self.reporter.build_report([])
        self.assertEqual(len(report.per_connector), 0)
        self.assertEqual(report.summary.total_connectors, 0)
        self.assertEqual(report.summary.s0_count, 0)
        self.assertEqual(report.summary.s1_count, 0)


class TestQualityReportSummary(unittest.TestCase):
    """Test QualityReportSummary dataclass."""

    def test_summary_creation(self):
        """Test creating QualityReportSummary instance."""
        summary = QualityReportSummary(
            total_connectors=5,
            s0_count=3,
            s1_count=1,
            s2_count=1,
            s3_count=0,
            fresh_count=4,
            stale_count=1,
            missing_count=0,
        )
        self.assertEqual(summary.total_connectors, 5)
        self.assertEqual(summary.s0_count, 3)
        self.assertEqual(summary.s1_count, 1)

    def test_summary_to_dict(self):
        """Test QualityReportSummary serialization to dict."""
        summary = QualityReportSummary(
            total_connectors=5,
            s0_count=3,
            s1_count=1,
            s2_count=1,
            s3_count=0,
            fresh_count=4,
            stale_count=1,
            missing_count=0,
        )
        data = summary.to_dict()
        self.assertEqual(data["total_connectors"], 5)
        self.assertEqual(data["s0_count"], 3)
        self.assertEqual(data["fresh_count"], 4)


if __name__ == "__main__":
    unittest.main()