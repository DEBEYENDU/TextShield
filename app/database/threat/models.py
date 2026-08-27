from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Text,
    Float,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class ThreatProvider(Base):
    """Database model for threat intelligence providers."""
    
    __tablename__ = "threat_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    version = Column(String, nullable=False, default="1.0.0")
    enabled = Column(Boolean, default=True, nullable=False)
    api_key_configured = Column(Boolean, default=False, nullable=False)
    ttl_seconds = Column(Integer, nullable=False, default=3600)
    timeout_seconds = Column(Integer, nullable=False, default=5)
    capabilities = Column(Text, nullable=True)  # JSON string
    config = Column(Text, nullable=True)  # JSON string for provider-specific config
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    # Relationships
    cache_entries = relationship("ThreatCacheEntry", back_populates="provider", cascade="all, delete-orphan")
    health_records = relationship("ProviderHealth", back_populates="provider", cascade="all, delete-orphan")
    rate_limit_records = relationship("ProviderRateLimit", back_populates="provider", cascade="all, delete-orphan")


class ThreatCacheEntry(Base):
    """Database model for threat intelligence cache entries."""
    
    __tablename__ = "threat_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    ioc_value = Column(String, nullable=False, index=True)
    ioc_type = Column(String, nullable=False)  # IOCType enum value
    provider = Column(String, nullable=False, index=True)
    indicator_data = Column(Text, nullable=False)  # JSON-serialized ThreatIndicator
    ttl_seconds = Column(Integer, nullable=False)
    cached_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    access_count = Column(Integer, default=0, nullable=False)
    
    # Composite index for fast lookups
    __table_args__ = (
        Index("idx_cache_ioc_provider", "ioc_value", "ioc_type", "provider"),
    )


class ProviderHealth(Base):
    """Database model for provider health tracking."""
    
    __tablename__ = "provider_health"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String, nullable=False, index=True)
    healthy = Column(Boolean, default=True, nullable=False)
    last_check = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    consecutive_successes = Column(Integer, default=0, nullable=False)
    consecutive_failures = Column(Integer, default=0, nullable=False)
    
    # Relationships
    provider = relationship("ThreatProvider", back_populates="health_records")


class ProviderRateLimit(Base):
    """Database model for provider rate limit tracking."""
    
    __tablename__ = "provider_rate_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String, nullable=False, index=True)
    period_start = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    requests_in_period = Column(Integer, default=0, nullable=False)
    daily_requests = Column(Integer, default=0, nullable=False)
    reset_at = Column(DateTime, default=lambda: datetime.now(timezone.utc) + __import__("datetime").timedelta(hours=1), nullable=False)
    
    # Relationships
    provider = relationship("ThreatProvider", back_populates="rate_limit_records")


class IOCRecord(Base):
    """Database model for IOC records."""
    
    __tablename__ = "ioc_records"
    
    id = Column(Integer, primary_key=True, index=True)
    ioc_value = Column(String, nullable=False, index=True)
    ioc_type = Column(String, nullable=False)  # IOCType enum value
    threat_level = Column(String, nullable=True)  # low, medium, high, critical
    confidence = Column(Float, default=0.0, nullable=False)
    times_seen = Column(Integer, default=1, nullable=False)
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    last_seen = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    provider_sources = Column(Text, nullable=True)  # JSON array of provider names
    metadata = Column(Text, nullable=True)  # JSON for additional metadata
    
    # Composite index
    __table_args__ = (
        Index("idx_ioc_value_type", "ioc_value", "ioc_type"),
    )


class ThreatEvent(Base):
    """Database model for threat events/audit trail."""
    
    __tablename__ = "threat_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)  # lookup, cache_hit, cache_miss, aggregation
    ioc_value = Column(String, nullable=True)
    ioc_type = Column(String, nullable=True)
    provider_name = Column(String, nullable=True)
    result = Column(String, nullable=True)  # success, failure, timeout, cached
    threat_detected = Column(Boolean, default=False, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    event_data = Column(Text, nullable=True)  # JSON for additional event data
    occurred_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_event_type", "event_type"),
        Index("idx_event_ioc", "ioc_value", "ioc_type"),
        Index("idx_event_provider", "provider_name"),
        Index("idx_event_occurred", "occurred_at"),
    )