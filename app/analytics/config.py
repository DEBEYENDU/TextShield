from __future__ import annotations

from typing import Dict, Any, Optional

from dataclasses import dataclass, field


@dataclass
class AnalyticsConfig:
    """Configuration for analytics and monitoring."""

    # History
    max_history_entries: int = 10000
    history_retention_days: int = 365
    enable_search: bool = True
    enable_filtering: bool = True
    default_page_size: int = 50

    # Analytics
    enable_model_analytics: bool = True
    enable_rag_analytics: bool = True
    enable_decision_analytics: bool = True
    enable_confidence_distribution: bool = True
    enable_risk_distribution: bool = True

    # Monitoring
    enable_system_monitoring: bool = True
    enable_performance_monitoring: bool = True
    monitoring_interval_seconds: int = 30
    max_cpu_threshold: float = 80.0
    max_memory_threshold: float = 80.0

    # Audit
    enable_audit_logging: bool = True
    log_configuration_changes: bool = True
    log_model_changes: bool = True
    log_analysis_execution: bool = True

    # Reporting
    export_formats: List[str] = field(default_factory=lambda: ["json", "csv", "markdown"])
    include_charts_in_reports: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_history_entries": self.max_history_entries,
            "history_retention_days": self.history_retention_days,
            "enable_search": self.enable_search,
            "enable_filtering": self.enable_filtering,
            "default_page_size": self.default_page_size,
            "enable_model_analytics": self.enable_model_analytics,
            "enable_rag_analytics": self.enable_rag_analytics,
            "enable_decision_analytics": self.enable_decision_analytics,
            "enable_confidence_distribution": self.enable_confidence_distribution,
            "enable_risk_distribution": self.enable_risk_distribution,
            "enable_system_monitoring": self.enable_system_monitoring,
            "enable_performance_monitoring": self.enable_performance_monitoring,
            "monitoring_interval_seconds": self.monitoring_interval_seconds,
            "max_cpu_threshold": self.max_cpu_threshold,
            "max_memory_threshold": self.max_memory_threshold,
            "enable_audit_logging": self.enable_audit_logging,
            "log_configuration_changes": self.log_configuration_changes,
            "log_model_changes": self.log_model_changes,
            "log_analysis_execution": self.log_analysis_execution,
            "export_formats": self.export_formats,
            "include_charts_in_reports": self.include_charts_in_reports,
        }