from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas import (
    AlertCreate, AlertUpdate, AlertAcknowledge, AlertResolve,
    AlertResponse, AlertDetailResponse, AlertListResponse, AlertStats
)
from app.services import AlertService, notification_service
from app.models import User, AlertStatus, AlertSeverity
from app.api.dependencies import get_current_user, require_user_or_admin, require_any_role

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    status: Optional[AlertStatus] = Query(None, description="Filter by status"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    source: Optional[str] = Query(None, description="Filter by source"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(require_any_role),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated list of alerts with optional filters"""
    alert_service = AlertService(db)
    alerts, total = await alert_service.get_alerts(
        status=status,
        severity=severity,
        source=source,
        search=search,
        page=page,
        page_size=page_size
    )
    
    return AlertListResponse(
        alerts=alerts,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/stats", response_model=AlertStats)
async def get_alert_stats(
    current_user: User = Depends(require_any_role),
    db: AsyncSession = Depends(get_db)
):
    """Get alert statistics"""
    alert_service = AlertService(db)
    return await alert_service.get_stats()


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(require_user_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert manually"""
    alert_service = AlertService(db)
    alert = await alert_service.create_alert(alert_data, source="manual")
    
    # Send notifications
    await notification_service.send_slack_notification(alert, action="fired")
    
    return alert


@router.get("/{alert_id}", response_model=AlertDetailResponse)
async def get_alert(
    alert_id: int,
    current_user: User = Depends(require_any_role),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific alert with history"""
    alert_service = AlertService(db)
    alert = await alert_service.get_alert_by_id(alert_id)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Build response with additional fields
    response = AlertDetailResponse(
        id=alert.id,
        fingerprint=alert.fingerprint,
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        status=alert.status,
        source=alert.source,
        labels=alert.labels,
        annotations=alert.annotations,
        fired_at=alert.fired_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        acknowledged_by_id=alert.acknowledged_by_id,
        resolved_by_id=alert.resolved_by_id,
        history=[
            {
                "id": h.id,
                "action": h.action,
                "comment": h.comment,
                "created_at": h.created_at,
                "user_id": h.user_id,
                "user_email": h.user.email if h.user else None
            }
            for h in alert.history
        ],
        acknowledged_by_email=alert.acknowledged_by.email if alert.acknowledged_by else None,
        resolved_by_email=alert.resolved_by.email if alert.resolved_by else None
    )
    
    return response


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: int,
    ack_data: AlertAcknowledge,
    current_user: User = Depends(require_user_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an alert"""
    alert_service = AlertService(db)
    alert = await alert_service.acknowledge_alert(
        alert_id=alert_id,
        user=current_user,
        comment=ack_data.comment
    )
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Send notifications
    await notification_service.send_slack_notification(alert, action="acknowledged")
    
    return alert


@router.post("/{alert_id}/resolve", response_model=AlertResponse)
async def resolve_alert(
    alert_id: int,
    resolve_data: AlertResolve,
    current_user: User = Depends(require_user_or_admin),
    db: AsyncSession = Depends(get_db)
):
    """Resolve an alert"""
    alert_service = AlertService(db)
    alert = await alert_service.resolve_alert(
        alert_id=alert_id,
        user=current_user,
        comment=resolve_data.comment
    )
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Send notifications
    await notification_service.send_slack_notification(alert, action="resolved")
    
    return alert
