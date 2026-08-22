from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import csv
import io


class ReportsGenerator:
    """Generator for various report formats."""

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

        # Filter records in range
        filtered = [
            r for r in records
            if start_date <= r.timestamp <= end_date
            if hasattr(r, "timestamp")
        ]

        # Compute statistics
        confidences = [
            r.metrics.get(MetricKeys.ANALYSIS_CONFIDENCE, 0.0)
            for r in filtered
            if hasattr(r, "metrics") and MetricKeys.ANALYSIS_CONFIDENCE in r.metrics
        ]
        risk_levels = [
            r.metrics.get(MetricKeys.ANALYSIS_RISK_LEVEL, "Unknown")
            for r in filtered
            if hasattr(r, "metrics") and MetricKeys.ANALYSIS_RISK_LEVEL in r.metrics
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
                level: risk_levels.count(level) for level in [
                    "Very Low", "Low", "Medium", "High", "Critical"
                ]
            }
            if risk_levels
            else {},
        }

    @staticmethod
    def generate_analytics_report(
        metrics_engine,
    ) -> Dict[str, Any]:
        """Generate analytics summary report."""
        records = metrics_engine.get_records()
        if not records:
            return {"error": "No records found"}

        return {
            "report_type": "analytics",
            "total_records": len(records),
            "records_by_type": metrics_engine.count_by_type(),
            "confidence_distribution": ReportsGenerator.compute_confidence_distribution(
                records
            ),
            "risk_distribution": ReportsGenerator.compute_risk_distribution(records),
            "common_intents": ReportsGenerator.compute_intent_frequencies(records),
            "common_behaviors": ReportsGenerator.compute_behavior_frequencies(records),
            "processing_time_stats": ReportsGenerator.compute_processing_time_stats(
                records
            ),
            "daily_usage": ReportsGenerator.compute_daily_usage(records),
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

    @staticmethod
    def export_to_csv(records: List[Any], filename: str) -> bool:
        """Export records to CSV file."""
        try:
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                # Header
                if records and hasattr(records[0], "metrics"):
                    writer.writerow(["timestamp", "type", "metrics"])
                    for r in records:
                        writer.writerow([
                            r.timestamp.isoformat() if hasattr(r, "timestamp") else "",
                            r.type if hasattr(r, "type") else "",
                            json.dumps(r.metrics) if hasattr(r, "metrics") else "",
                        ])
                return True
        except Exception:
            return False

    @staticmethod
    def export_to_json(records: List[Any], filename: str) -> bool:
        """Export records to JSON file."""
        try:
            with open(filename, "w") as f:
                data = [
                    r.to_dict() if hasattr(r, "to_dict") else {}
                    for r in records
                ]
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

    @staticmethod
    def export_to_markdown(records: List[Any], filename: str) -> bool:
        """Export records to Markdown file."""
        try:
            with open(filename, "w") as f:
                f.write("# Records Export\n\n")
                f.write(f"- Records: {len(records)}\n\n")
                f.write("---\n\n")
                f.write(json.dumps(
                    [r.to_dict() if hasattr(r, "to_dict") else {} for r in records],
                    indent=2
                ))
            return True
        except Exception:
            return False


# Predefined metric keys
class MetricKeys:
    """Predefined metric key constants."""
    ANALYSIS_CONFIDENCE = "analysis_confidence"
    ANALYSIS_RISK_SCORE = "analysis_risk_score"
    ANALYSIS_PROCESSING_TIME = "analysis_processing_time"
    ANALYSIS_CLASSIFICATION = "analysis_classification"
    ANALYSIS_RISK_LEVEL = "analysis_risk_level"
    MODEL_CONFIDENCE = "model_confidence"
    MODEL_LATENCY = "model_latency"
    SYSTEM_CPU_USAGE = "system_cpu_usage"
    SYSTEM_MEMORY_USAGE = "system_memory_usage"