from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter


class StatisticsEngine:
    """Engine for computing statistics from metrics data."""

    @staticmethod
    def compute_confidence_distribution(
        records: List[Any], bins: int = 10
    ) -> Dict[str, Any]:
        """Compute confidence distribution from analysis records."""
        confidences = []
        for r in records:
            if hasattr(r, "metrics") and "analysis_confidence" in r.metrics:
                confidences.append(r.metrics["analysis_confidence"])

        if not confidences:
            return {"error": "No confidence data found"}

        min_val = min(confidences)
        max_val = max(confidences)
        bin_width = (max_val - min_val) / bins if bins > 0 else 1

        distribution = {}
        for i in range(bins):
            bin_lower = min_val + i * bin_width
            bin_upper = min_val + (i + 1) * bin_width
            count = sum(1 for c in confidences if bin_lower <= c < bin_upper)
            if i == bins - 1:
                count += sum(1 for c in confidences if c == bin_upper)

            distribution[f"{bin_lower:.2f}-{bin_upper:.2f}"] = count

        return {
            "min": min_val,
            "max": max_val,
            "average": sum(confidences) / len(confidences) if confidences else 0,
            "distribution": distribution,
            "total_analyses": len(confidences),
        }

    @staticmethod
    def compute_risk_distribution(
        records: List[Any], risk_levels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compute risk distribution from analysis records."""
        if risk_levels is None:
            risk_levels = ["Very Low", "Low", "Medium", "High", "Critical"]

        counts = Counter()
        for r in records:
            if hasattr(r, "metrics") and "analysis_risk_level" in r.metrics:
                risk = r.metrics["analysis_risk_level"]
                counts[risk] += 1

        total = sum(counts.values())
        distribution = {}
        for level in risk_levels:
            distribution[level] = counts.get(level, 0)
            distribution[f"{level}_percentage"] = (
                (distribution[level] / total * 100) if total > 0 else 0
            )

        return {
            "distribution": distribution,
            "total_analyses": total,
            "risk_levels": risk_levels,
        }

    @staticmethod
    def compute_intent_frequencies(
        records: List[Any], top_n: int = 10
    ) -> Dict[str, Any]:
        """Compute most common intents from analysis records."""
        intents = Counter()
        for r in records:
            if hasattr(r, "metadata") and "primary_intent" in r.metadata:
                intents[r.metadata["primary_intent"]] += 1
            elif hasattr(r, "metrics") and "intent" in r.metrics:
                intent = r.metrics["intent"]
                if isinstance(intent, str):
                    intents[intent] += 1
                elif isinstance(intent, dict):
                    primary = intent.get("primary_intent", "")
                    if primary:
                        intents[primary] += 1

        most_common = intents.most_common(top_n)
        return {
            "intents": {k: v for k, v in most_common},
            "total_analyses": sum(intents.values()),
        }

    @staticmethod
    def compute_behavior_frequencies(
        records: List[Any], top_n: int = 10
    ) -> Dict[str, Any]:
        """Compute most common behaviors from analysis records."""
        behaviors = Counter()
        for r in records:
            if hasattr(r, "metadata") and "urgency_level" in r.metadata:
                behaviors[r.metadata["urgency_level"]] += 1
            elif hasattr(r, "metrics") and "behavior" in r.metrics:
                behavior = r.metrics["behavior"]
                if isinstance(behavior, str):
                    behaviors[behavior] += 1

        most_common = behaviors.most_common(top_n)
        return {
            "behaviors": {k: v for k, v in most_common},
            "total_analyses": sum(behaviors.values()),
        }

    @staticmethod
    def compute_processing_time_stats(
        records: List[Any],
    ) -> Dict[str, Any]:
        """Compute processing time statistics."""
        times = []
        for r in records:
            if hasattr(r, "metrics") and "analysis_processing_time" in r.metrics:
                times.append(r.metrics["analysis_processing_time"])

        if not times:
            return {"error": "No processing time data found"}

        return {
            "min": min(times),
            "max": max(times),
            "average": sum(times) / len(times),
            "median": sorted(times)[len(times) // 2],
            "p95": sorted(times)[int(0.95 * len(times))],
            "p99": sorted(times)[int(0.99 * len(times))],
            "total_analyses": len(times),
        }

    @staticmethod
    def compute_daily_usage(
        records: List[Any],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Compute daily usage statistics."""
        if start_date is None:
            from datetime import datetime, timedelta

            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        daily_counts = Counter()
        for r in records:
            if start_date <= r.timestamp <= end_date:
                day_key = r.timestamp.strftime("%Y-%m-%d")
                daily_counts[day_key] += 1

        date_range = []
        from datetime import datetime, timedelta

        current = start_date
        while current <= end_date:
            date_range.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        filled_distribution = {day: daily_counts.get(day, 0) for day in date_range}

        return {
            "daily_usage": filled_distribution,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "total_analyses": sum(daily_counts.values()),
        }
