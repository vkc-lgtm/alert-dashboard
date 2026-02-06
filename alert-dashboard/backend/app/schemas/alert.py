from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.alert import AlertSeverity, AlertStatus


# Base schemas
class AlertBase(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    severity: AlertSeverity = AlertSeverity.WARNING
    labels: Optional[Dict[str, Any]] = None
    annotations: Optional[Dict[str, Any]] = None


# Create schemas
class AlertCreate(AlertBase):
    fingerprint: Optional[str] = None
    source: str = "manual"


# Update schemas
class AlertUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[AlertSeverity] = None


class AlertAcknowledge(BaseModel):
    comment: Optional[str] = None


class AlertResolve(BaseModel):
    comment: Optional[str] = None


# History schemas
class AlertHistoryResponse(BaseModel):
    id: int
    action: str
    comment: Optional[str] = None
    created_at: datetime
    user_id: Optional[int] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True


# Response schemas
class AlertResponse(AlertBase):
    id: int
    fingerprint: str
    status: AlertStatus
    source: str
    fired_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    acknowledged_by_id: Optional[int] = None
    resolved_by_id: Optional[int] = None

    class Config:
        from_attributes = True


class AlertDetailResponse(AlertResponse):
    history: List[AlertHistoryResponse] = []
    acknowledged_by_email: Optional[str] = None
    resolved_by_email: Optional[str] = None


class AlertListResponse(BaseModel):
    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int


# Stats schemas
class AlertStats(BaseModel):
    total: int
    firing: int
    acknowledged: int
    resolved: int
    critical: int
    warning: int
    info: int


# Grafana webhook schemas
class GrafanaAlert(BaseModel):
    status: str  # "firing" or "resolved"
    labels: Dict[str, str] = {}
    annotations: Dict[str, str] = {}
    startsAt: Optional[str] = None
    endsAt: Optional[str] = None
    generatorURL: Optional[str] = None
    fingerprint: Optional[str] = None
    values: Optional[Dict[str, Any]] = None


class GrafanaWebhookPayload(BaseModel):
    receiver: Optional[str] = None
    status: str  # "firing" or "resolved"
    alerts: List[GrafanaAlert] = []
    groupLabels: Dict[str, str] = {}
    commonLabels: Dict[str, str] = {}
    commonAnnotations: Dict[str, str] = {}
    externalURL: Optional[str] = None
    version: Optional[str] = None
    groupKey: Optional[str] = None
    truncatedAlerts: Optional[int] = None
    title: Optional[str] = None
    state: Optional[str] = None
    message: Optional[str] = None
