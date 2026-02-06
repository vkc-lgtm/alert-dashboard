import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Alert, AlertHistory, AlertStatus, AlertSeverity, User
from app.schemas import AlertCreate, AlertStats
from app.core.config import settings


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _generate_fingerprint(self, title: str, labels: dict) -> str:
        """Generate a unique fingerprint for deduplication"""
        content = f"{title}:{json.dumps(labels, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    async def create_alert(
        self,
        alert_data: AlertCreate,
        source: str = "manual"
    ) -> Alert:
        """Create a new alert or update existing one based on fingerprint"""
        
        # Generate fingerprint if not provided
        fingerprint = alert_data.fingerprint
        if not fingerprint:
            fingerprint = self._generate_fingerprint(
                alert_data.title,
                alert_data.labels or {}
            )

        # Check for existing active alert with same fingerprint (deduplication)
        existing = await self.get_active_alert_by_fingerprint(fingerprint)
        
        if existing:
            # Update the existing alert's timestamp
            existing.updated_at = datetime.utcnow()
            await self.db.commit()
            return existing

        # Create new alert
        alert = Alert(
            fingerprint=fingerprint,
            title=alert_data.title,
            description=alert_data.description,
            severity=alert_data.severity,
            status=AlertStatus.FIRING,
            source=source,
            labels=json.dumps(alert_data.labels) if alert_data.labels else None,
            annotations=json.dumps(alert_data.annotations) if alert_data.annotations else None,
            fired_at=datetime.utcnow()
        )
        
        self.db.add(alert)
        await self.db.flush()

        # Add history entry
        history = AlertHistory(
            alert_id=alert.id,
            action="created",
            comment=f"Alert created from {source}"
        )
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(alert)
        
        return alert

    async def get_active_alert_by_fingerprint(self, fingerprint: str) -> Optional[Alert]:
        """Get an active (firing or acknowledged) alert by fingerprint"""
        dedup_window = datetime.utcnow() - timedelta(minutes=settings.ALERT_DEDUP_WINDOW_MINUTES)
        
        result = await self.db.execute(
            select(Alert).where(
                and_(
                    Alert.fingerprint == fingerprint,
                    Alert.status.in_([AlertStatus.FIRING, AlertStatus.ACKNOWLEDGED]),
                    Alert.updated_at >= dedup_window
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_alert_by_id(self, alert_id: int) -> Optional[Alert]:
        """Get an alert by ID with history"""
        result = await self.db.execute(
            select(Alert)
            .options(selectinload(Alert.history))
            .where(Alert.id == alert_id)
        )
        return result.scalar_one_or_none()

    async def get_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Alert], int]:
        """Get paginated list of alerts with filters"""
        query = select(Alert)
        count_query = select(func.count(Alert.id))

        # Apply filters
        conditions = []
        if status:
            conditions.append(Alert.status == status)
        if severity:
            conditions.append(Alert.severity == severity)
        if source:
            conditions.append(Alert.source == source)
        if search:
            conditions.append(
                or_(
                    Alert.title.ilike(f"%{search}%"),
                    Alert.description.ilike(f"%{search}%")
                )
            )

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination and ordering
        query = query.order_by(Alert.fired_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        alerts = result.scalars().all()

        return list(alerts), total

    async def acknowledge_alert(
        self,
        alert_id: int,
        user: User,
        comment: Optional[str] = None
    ) -> Optional[Alert]:
        """Acknowledge an alert"""
        alert = await self.get_alert_by_id(alert_id)
        if not alert:
            return None

        if alert.status != AlertStatus.FIRING:
            return alert  # Already acknowledged or resolved

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by_id = user.id
        alert.updated_at = datetime.utcnow()

        # Add history entry
        history = AlertHistory(
            alert_id=alert.id,
            action="acknowledged",
            comment=comment,
            user_id=user.id
        )
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(alert)

        return alert

    async def resolve_alert(
        self,
        alert_id: int,
        user: Optional[User] = None,
        comment: Optional[str] = None,
        auto: bool = False
    ) -> Optional[Alert]:
        """Resolve an alert"""
        alert = await self.get_alert_by_id(alert_id)
        if not alert:
            return None

        if alert.status == AlertStatus.RESOLVED:
            return alert  # Already resolved

        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by_id = user.id if user else None
        alert.updated_at = datetime.utcnow()

        # Add history entry
        action = "auto_resolved" if auto else "resolved"
        history = AlertHistory(
            alert_id=alert.id,
            action=action,
            comment=comment or ("Auto-resolved by system" if auto else None),
            user_id=user.id if user else None
        )
        self.db.add(history)
        await self.db.commit()
        await self.db.refresh(alert)

        return alert

    async def get_stats(self) -> AlertStats:
        """Get alert statistics"""
        # Total count
        total_result = await self.db.execute(select(func.count(Alert.id)))
        total = total_result.scalar()

        # By status
        status_query = select(Alert.status, func.count(Alert.id)).group_by(Alert.status)
        status_result = await self.db.execute(status_query)
        status_counts = {row[0]: row[1] for row in status_result.all()}

        # By severity (only firing and acknowledged)
        severity_query = select(Alert.severity, func.count(Alert.id)).where(
            Alert.status.in_([AlertStatus.FIRING, AlertStatus.ACKNOWLEDGED])
        ).group_by(Alert.severity)
        severity_result = await self.db.execute(severity_query)
        severity_counts = {row[0]: row[1] for row in severity_result.all()}

        return AlertStats(
            total=total,
            firing=status_counts.get(AlertStatus.FIRING, 0),
            acknowledged=status_counts.get(AlertStatus.ACKNOWLEDGED, 0),
            resolved=status_counts.get(AlertStatus.RESOLVED, 0),
            critical=severity_counts.get(AlertSeverity.CRITICAL, 0),
            warning=severity_counts.get(AlertSeverity.WARNING, 0),
            info=severity_counts.get(AlertSeverity.INFO, 0)
        )

    async def resolve_alert_by_fingerprint(self, fingerprint: str) -> Optional[Alert]:
        """Resolve an alert by its fingerprint (used by webhooks)"""
        alert = await self.get_active_alert_by_fingerprint(fingerprint)
        if alert:
            return await self.resolve_alert(alert.id, auto=True, comment="Resolved via webhook")
        return None
