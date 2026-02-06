import json
import hashlib
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas import GrafanaWebhookPayload, AlertCreate
from app.services import AlertService, notification_service
from app.models import AlertSeverity

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key for webhook authentication"""
    if not x_api_key or x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key"
        )
    return x_api_key


def map_grafana_severity(labels: dict) -> AlertSeverity:
    """Map Grafana alert labels to severity"""
    severity_label = labels.get("severity", "").lower()
    
    if severity_label in ["critical", "emergency", "fatal"]:
        return AlertSeverity.CRITICAL
    elif severity_label in ["warning", "warn"]:
        return AlertSeverity.WARNING
    elif severity_label in ["info", "informational", "notice"]:
        return AlertSeverity.INFO
    
    # Default based on alertname or other indicators
    alertname = labels.get("alertname", "").lower()
    if "critical" in alertname or "down" in alertname:
        return AlertSeverity.CRITICAL
    elif "warning" in alertname:
        return AlertSeverity.WARNING
    
    return AlertSeverity.WARNING


@router.post("/grafana")
async def grafana_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Receive alerts from Grafana.
    
    Grafana sends alerts in a specific format. This endpoint handles both
    the legacy format and the newer unified alerting format.
    """
    alert_service = AlertService(db)
    
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # Handle both single alert and batch formats
    alerts_processed = []
    
    # Check if it's the unified alerting format (has 'alerts' array)
    if "alerts" in body:
        payload = GrafanaWebhookPayload(**body)
        
        for grafana_alert in payload.alerts:
            # Generate fingerprint
            fingerprint = grafana_alert.fingerprint
            if not fingerprint:
                content = f"{grafana_alert.labels}"
                fingerprint = hashlib.md5(content.encode()).hexdigest()
            
            # Get title from labels or annotations
            title = grafana_alert.labels.get("alertname", "Grafana Alert")
            if payload.commonAnnotations.get("summary"):
                title = payload.commonAnnotations["summary"]
            elif grafana_alert.annotations.get("summary"):
                title = grafana_alert.annotations["summary"]
            
            # Get description
            description = grafana_alert.annotations.get("description", "")
            if not description and payload.commonAnnotations.get("description"):
                description = payload.commonAnnotations["description"]
            
            # Determine severity
            all_labels = {**payload.commonLabels, **grafana_alert.labels}
            severity = map_grafana_severity(all_labels)
            
            if grafana_alert.status == "firing":
                # Create or update alert
                alert_data = AlertCreate(
                    fingerprint=fingerprint,
                    title=title,
                    description=description,
                    severity=severity,
                    labels=all_labels,
                    annotations={**payload.commonAnnotations, **grafana_alert.annotations},
                    source="grafana"
                )
                alert = await alert_service.create_alert(alert_data, source="grafana")
                alerts_processed.append({
                    "id": alert.id,
                    "fingerprint": fingerprint,
                    "action": "created" if alert.status.value == "firing" else "deduplicated"
                })
                
                # Send notifications
                await notification_service.send_slack_notification(alert, action="fired")
                
            elif grafana_alert.status == "resolved":
                # Resolve existing alert
                alert = await alert_service.resolve_alert_by_fingerprint(fingerprint)
                if alert:
                    alerts_processed.append({
                        "id": alert.id,
                        "fingerprint": fingerprint,
                        "action": "resolved"
                    })
                    await notification_service.send_slack_notification(alert, action="resolved")
    
    # Handle legacy Grafana webhook format
    elif "state" in body or "title" in body:
        title = body.get("title", body.get("ruleName", "Grafana Alert"))
        message = body.get("message", body.get("evalMatches", ""))
        state = body.get("state", "alerting")
        
        # Generate fingerprint from rule name
        rule_id = body.get("ruleId", body.get("ruleUrl", title))
        fingerprint = hashlib.md5(str(rule_id).encode()).hexdigest()
        
        if state in ["alerting", "pending"]:
            alert_data = AlertCreate(
                fingerprint=fingerprint,
                title=title,
                description=str(message),
                severity=AlertSeverity.WARNING,
                labels={"ruleName": title},
                annotations=body,
                source="grafana"
            )
            alert = await alert_service.create_alert(alert_data, source="grafana")
            alerts_processed.append({
                "id": alert.id,
                "fingerprint": fingerprint,
                "action": "created"
            })
            await notification_service.send_slack_notification(alert, action="fired")
            
        elif state in ["ok", "no_data"]:
            alert = await alert_service.resolve_alert_by_fingerprint(fingerprint)
            if alert:
                alerts_processed.append({
                    "id": alert.id,
                    "fingerprint": fingerprint,
                    "action": "resolved"
                })
                await notification_service.send_slack_notification(alert, action="resolved")
    
    return {
        "status": "ok",
        "processed": len(alerts_processed),
        "alerts": alerts_processed
    }


@router.post("/generic")
async def generic_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """
    Generic webhook endpoint for custom integrations.
    
    Expected payload:
    {
        "title": "Alert title",
        "description": "Alert description",
        "severity": "critical|warning|info",
        "labels": {"key": "value"},
        "fingerprint": "optional-unique-id",
        "status": "firing|resolved"
    }
    """
    alert_service = AlertService(db)
    
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    title = body.get("title", "Generic Alert")
    description = body.get("description", "")
    severity_str = body.get("severity", "warning").lower()
    labels = body.get("labels", {})
    fingerprint = body.get("fingerprint")
    alert_status = body.get("status", "firing").lower()
    
    # Map severity
    severity_map = {
        "critical": AlertSeverity.CRITICAL,
        "warning": AlertSeverity.WARNING,
        "info": AlertSeverity.INFO
    }
    severity = severity_map.get(severity_str, AlertSeverity.WARNING)
    
    if alert_status == "firing":
        alert_data = AlertCreate(
            fingerprint=fingerprint,
            title=title,
            description=description,
            severity=severity,
            labels=labels,
            source="generic"
        )
        alert = await alert_service.create_alert(alert_data, source="generic")
        await notification_service.send_slack_notification(alert, action="fired")
        
        return {
            "status": "ok",
            "alert_id": alert.id,
            "action": "created"
        }
    
    elif alert_status == "resolved" and fingerprint:
        alert = await alert_service.resolve_alert_by_fingerprint(fingerprint)
        if alert:
            await notification_service.send_slack_notification(alert, action="resolved")
            return {
                "status": "ok",
                "alert_id": alert.id,
                "action": "resolved"
            }
        return {
            "status": "ok",
            "action": "no_matching_alert"
        }
    
    return {"status": "ok", "action": "ignored"}
