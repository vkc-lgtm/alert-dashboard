import httpx
from typing import Optional
from app.core.config import settings
from app.models import Alert, AlertSeverity


class NotificationService:
    """Service for sending notifications via email and Slack"""

    @staticmethod
    def _get_severity_color(severity: AlertSeverity) -> str:
        """Get color for Slack message based on severity"""
        colors = {
            AlertSeverity.CRITICAL: "#dc3545",  # Red
            AlertSeverity.WARNING: "#ffc107",   # Yellow
            AlertSeverity.INFO: "#17a2b8"       # Blue
        }
        return colors.get(severity, "#6c757d")

    @staticmethod
    def _get_severity_emoji(severity: AlertSeverity) -> str:
        """Get emoji for severity"""
        emojis = {
            AlertSeverity.CRITICAL: "🔴",
            AlertSeverity.WARNING: "🟡",
            AlertSeverity.INFO: "🔵"
        }
        return emojis.get(severity, "⚪")

    async def send_slack_notification(
        self,
        alert: Alert,
        action: str = "fired"
    ) -> bool:
        """Send a Slack notification for an alert"""
        if not settings.SLACK_ENABLED or not settings.SLACK_WEBHOOK_URL:
            return False

        emoji = self._get_severity_emoji(alert.severity)
        color = self._get_severity_color(alert.severity)
        
        action_text = {
            "fired": f"{emoji} *Alert Fired*",
            "acknowledged": "✅ *Alert Acknowledged*",
            "resolved": "✔️ *Alert Resolved*"
        }.get(action, f"*Alert {action}*")

        message = {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"{action_text}\n*{alert.title}*"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Severity:*\n{alert.severity.value.upper()}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Source:*\n{alert.source}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Status:*\n{alert.status.value.upper()}"
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Alert ID:*\n{alert.id}"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

        if alert.description:
            message["attachments"][0]["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{alert.description[:500]}"
                }
            })

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.SLACK_WEBHOOK_URL,
                    json=message,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
            return False

    async def send_email_notification(
        self,
        alert: Alert,
        recipient_email: str,
        action: str = "fired"
    ) -> bool:
        """Send an email notification for an alert"""
        if not settings.EMAIL_ENABLED:
            return False

        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            emoji = self._get_severity_emoji(alert.severity)
            subject = f"[{alert.severity.value.upper()}] {alert.title}"

            # Create HTML email
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: {'#dc3545' if alert.severity == AlertSeverity.CRITICAL else '#ffc107' if alert.severity == AlertSeverity.WARNING else '#17a2b8'};">
                    {emoji} Alert {action.capitalize()}
                </h2>
                <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Title</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{alert.title}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Severity</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{alert.severity.value.upper()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Status</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{alert.status.value.upper()}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Source</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{alert.source}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold;">Description</td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{alert.description or 'N/A'}</td>
                    </tr>
                </table>
            </body>
            </html>
            """

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = recipient_email
            msg.attach(MIMEText(html_content, "html"))

            await aiosmtplib.send(
                msg,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True
            )
            return True
        except Exception as e:
            print(f"Failed to send email notification: {e}")
            return False


# Singleton instance
notification_service = NotificationService()
