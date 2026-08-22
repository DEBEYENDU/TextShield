from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import csv
import io


class AnalyticsExporter:
    """Exporter for analytics data in various formats."""

    @staticmethod
    def export_history_to_csv(history, filename: str) -> bool:
        """Export history to CSV file."""
        try:
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                if history._records:
                    writer.writerow(["timestamp", "classification", "risk_level", "confidence"])
                    for record in history._records:
                        writer.writerow([
                            record.get("timestamp", ""),
                            record.get("classification", ""),
                            record.get("risk_level", ""),
                            record.get("confidence", 0),
                        ])
            return True
        except Exception:
            return False

    @staticmethod
    def export_history_to_json(history, filename: str) -> bool:
        """Export history to JSON file."""
        try:
            with open(filename, "w") as f:
                json.dump(history._records, f, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def export_analytics_to_json(metrics_engine, filename: str) -> bool:
        """Export analytics data to JSON file."""
        try:
            records = metrics_engine.get_records()
            with open(filename, "w") as f:
                json.dump(records, f, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def export_analytics_to_markdown(metrics_engine, filename: str) -> bool:
        """Export analytics to Markdown file."""
        try:
            reports = ReportsGenerator.generate_analytics_report(metrics_engine)
            with open(filename, "w") as f:
                f.write(json.dumps(reports, indent=2))
            return True
        except Exception:
            return False

    @staticmethod
    def export_explanation_to_json(explanation, filename: str) -> bool:
        """Export explanation record to JSON file."""
        try:
            with open(filename, "w") as f:
                if hasattr(explanation, "to_dict"):
                    json.dump(explanation.to_dict(), f, indent=2)
                else:
                    json.dump(explanation, f, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def export_explanation_to_markdown(explanation, filename: str) -> bool:
        """Export explanation to Markdown file."""
        try:
            from analytics.explainability import ExplainabilityReportGenerator
            md = ReportsGenerator.generate_analytics_report(
                type("obj", (object,), {"get_records": lambda self: []})()
            )
            with open(filename, "w") as f:
                f.write(ExplainabilityReportGenerator.generate_evidence_report(
                    [explanation] if explanation else []
                ))
            return True
        except Exception:
            return False


class ReportsGenerator:
    """Generator for various report formats (duplicate from metrics module)."""

    @staticmethod
    def generate_analysis_report(
        records: List[Any],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate an analysis summary report."""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        filtered = [
            r for r in records
            if start_date <= r.timestamp <= end_date
            if hasattr(r, "timestamp")
        ]

        confidences = [
            r.metrics.get(MetricKeys.ANALYSIS_CONFIDENCE, 0.0)
            for r in filtered
            if hasattr(r, "metrics") and MetricKeys.ANALYSIS_CONFIDENCE in r.metrics
        ]

        return {
            "report_type": "analysis",
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "total_analyses": len(filtered),
            "confidence_stats": {
                "average": sum(confidences) / len(confidences) if confidences else 0,
                "min": min(confidences) if confidences else 0,
                "max": max(confidences) if confidences else 0,
            } if confidences else {"average": 0, "min": 0, "max": 0},
            "risk_distribution": {
                level: sum(1 for r in filtered
                          if r.metrics.get(MetricKeys.ANALYSIS_RISK_LEVEL) == level)
                for level in ["Very Low", "Low", "Medium", "High", "Critical"]
            } if filtered else {},
        }

    @staticmethod
    def generate_system_report(
        system_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate system health report."""
        return {
            "report_type": "system",
            "timestamp": datetime.utcnow().isoformat(),
            "system_metrics": system_metrics,
        }