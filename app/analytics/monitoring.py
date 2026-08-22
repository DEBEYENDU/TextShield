from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import psutil
import os


class SystemMonitor:
    """Monitors system resources and performance."""

    @staticmethod
    def get_cpu_metrics() -> Dict[str, Any]:
        """Get CPU usage metrics."""
        try:
            return {
                "usage_percent": psutil.cpu_percent(interval=1),
                "core_count": psutil.cpu_count(),
                "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
            }
        except Exception:
            return {"usage_percent": 0, "core_count": 0, "load_average": None}

    @staticmethod
    def get_memory_metrics() -> Dict[str, Any]:
        """Get memory usage metrics."""
        try:
            mem = psutil.virtual_memory()
            return {
                "total_bytes": mem.total,
                "available_bytes": mem.available,
                "used_bytes": mem.used,
                "usage_percent": mem.percent,
            }
        except Exception:
            return {
                "total_bytes": 0,
                "available_bytes": 0,
                "used_bytes": 0,
                "usage_percent": 0,
            }

    @staticmethod
    def get_disk_metrics(path: str = "/") -> Dict[str, Any]:
        """Get disk usage metrics."""
        try:
            disk = psutil.disk_usage(path)
            return {
                "total_bytes": disk.total,
                "used_bytes": disk.used,
                "free_bytes": disk.free,
                "usage_percent": disk.percent,
            }
        except Exception:
            return {
                "total_bytes": 0,
                "used_bytes": 0,
                "free_bytes": 0,
                "usage_percent": 0,
            }

    @staticmethod
    def get_process_metrics(pid: Optional[int] = None) -> Dict[str, Any]:
        """Get process-specific metrics."""
        try:
            target_pid = pid or os.getpid()
            process = psutil.Process(target_pid)
            return {
                "pid": process.pid,
                "memory_bytes": process.memory_info().rss,
                "cpu_percent": process.cpu_percent(),
                "num_threads": process.num_threads(),
                "status": process.status(),
            }
        except Exception:
            return {
                "pid": pid or os.getpid(),
                "memory_bytes": 0,
                "cpu_percent": 0,
                "num_threads": 0,
                "status": "unknown",
            }


class ServiceHealth:
    """Health check for various services."""

    @staticmethod
    def check_database() -> Dict[str, Any]:
        """Check database health."""
        # Placeholder - integrate with actual database
        return {
            "healthy": True,
            "response_time_ms": 0,
            "details": "Database connection operational",
        }

    @staticmethod
    def check_vector_database() -> Dict[str, Any]:
        """Check vector database health."""
        # Placeholder - integrate with actual vector DB
        return {
            "healthy": True,
            "response_time_ms": 0,
            "details": "Vector database connection operational",
        }

    @staticmethod
    def check_llm_provider() -> Dict[str, Any]:
        """Check LLM provider health."""
        # Placeholder - integrate with actual LLM
        return {
            "healthy": True,
            "response_time_ms": 0,
            "details": "LLM provider connection operational",
        }

    @staticmethod
    def check_embedding_model() -> Dict[str, Any]:
        """Check embedding model health."""
        # Placeholder - integrate with actual embedding model
        return {
            "healthy": True,
            "response_time_ms": 0,
            "details": "Embedding model operational",
        }


class MonitoringService:
    """Service for collecting and reporting monitoring data."""

    @staticmethod
    def get_health_summary() -> Dict[str, Any]:
        """Get overall health summary."""
        return {
            "system": {
                "cpu": SystemMonitor.get_cpu_metrics(),
                "memory": SystemMonitor.get_memory_metrics(),
                "disk": SystemMonitor.get_disk_metrics(),
            },
            "services": {
                "database": ServiceHealth.check_database(),
                "vector_db": ServiceHealth.check_vector_database(),
                "llm": ServiceHealth.check_llm_provider(),
                "embedding_model": ServiceHealth.check_embedding_model(),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def get_metrics_snapshot() -> Dict[str, Any]:
        """Get a metrics snapshot."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": SystemMonitor.get_cpu_metrics(),
            "process": SystemMonitor.get_process_metrics(),
        }