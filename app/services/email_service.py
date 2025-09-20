from typing import List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings


class EmailService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)

    async def send_approval_request_notification(self, to_email: str, from_user: str, file_names: List[str]):
        if not settings.EMAIL_SERVICE_ENABLED:
            return

        subject = "You have a new approval request"
        body = f"We would like to inform you that {from_user} submitted an approval request containing {', '.join(file_names)}. Please visit {settings.UI_BASE_URL}/inbox to check it."
        
        await self._send_email_async(to_email, subject, body)

    async def send_approval_request_deleted_notification(self, to_email: str, from_user: str, file_names: List[str]):
        if not settings.EMAIL_SERVICE_ENABLED:
            return

        subject = "An approval request was deleted"
        body = f"We would like to inform you that {from_user} deleted the approval request containing {', '.join(file_names)}."
        
        await self._send_email_async(to_email, subject, body)

    async def send_approval_request_reviewed_notification(self, to_email: str, reviewer: str, file_names: List[str]):
        if not settings.EMAIL_SERVICE_ENABLED:
            return

        subject = "Your approval request was reviewed"
        body = f"We would like to inform you that {reviewer} reviewed the approval request containing {', '.join(file_names)}. Please visit {settings.UI_BASE_URL}/sent to check it."
        
        await self._send_email_async(to_email, subject, body)

    async def send_confirmation_email(self, to_email: str, confirmation_link: str):
        if not settings.EMAIL_SERVICE_ENABLED:
            return

        subject = "Confirm your email address to get started on click2approve"
        body = f"Please click the following link to confirm your email: {confirmation_link}"
        
        await self._send_email_async(to_email, subject, body)

    async def send_password_reset_email(self, to_email: str, reset_link: str):
        if not settings.EMAIL_SERVICE_ENABLED:
            return

        subject = "Reset your password on click2approve"
        body = f"Please click the following link to reset your password: {reset_link}"
        
        await self._send_email_async(to_email, subject, body)

    async def _send_email_async(self, to_email: str, subject: str, body: str):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, self._send_email, to_email, subject, body)

    def _send_email(self, to_email: str, subject: str, body: str):
        if not all([settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD]):
            print(f"Email would be sent to {to_email}: {subject}")
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_DEFAULT_FROM or settings.EMAIL_USERNAME
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
            server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(settings.EMAIL_USERNAME, to_email, text)
            server.quit()
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")