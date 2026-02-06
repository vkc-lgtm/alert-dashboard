import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.database import Base


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class AlertStatus(str, enum.Enum):
    FIRING = "firing"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    fingerprint = Column(String(255), index=True, nullable=False)  # For deduplication
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(Enum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.FIRING, nullable=False)
    source = Column(String(100), default="grafana", nullable=False)  # grafana, prometheus, custom
    
    # Labels and annotations (stored as JSON string)
    labels = Column(Text, nullable=True)
    annotations = Column(Text, nullable=True)
    
    # Timestamps
    fired_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    acknowledged_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_id], backref="acknowledged_alerts")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id], backref="resolved_alerts")
    
    # Alert history
    history = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_alerts_status_severity", "status", "severity"),
        Index("ix_alerts_fired_at", "fired_at"),
    )


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)  # created, acknowledged, resolved, escalated, comment
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User", backref="alert_actions")
    alert = relationship("Alert", back_populates="history")
