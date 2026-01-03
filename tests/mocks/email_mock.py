"""
Mock email service implementation for testing.
File: tests/mocks/email_mock.py
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MockEmail:
    """Represents a sent email."""
    to: str
    subject: str
    html_body: str
    text_body: Optional[str] = None
    from_email: str = "noreply@test.com"
    from_name: str = "Test App"
    sent_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MockEmailService:
    """
    Mock email service for testing.

    Stores sent emails in memory for verification.
    Can be configured to fail for testing error handling.
    """

    def __init__(
        self,
        should_fail: bool = False,
        fail_after: int = 0
    ):
        self.should_fail = should_fail
        self.fail_after = fail_after
        self.sent_emails: List[MockEmail] = []
        self.send_count = 0

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        from_email: str = "noreply@test.com",
        from_name: str = "Test App",
        **kwargs
    ) -> Dict[str, Any]:
        """Send a mock email."""
        self.send_count += 1

        # Simulate failures if configured
        if self.should_fail:
            if self.fail_after == 0 or self.send_count > self.fail_after:
                raise Exception("Mock email send failure")

        email = MockEmail(
            to=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            from_email=from_email,
            from_name=from_name,
            metadata=kwargs
        )
        self.sent_emails.append(email)

        return {
            "id": f"mock_email_{len(self.sent_emails)}",
            "status": "sent",
            "to": to
        }

    async def send_password_reset_email(
        self,
        to: str,
        reset_link: str,
        user_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a password reset email."""
        subject = "Reset Your Password"
        html_body = f"""
        <h1>Password Reset Request</h1>
        <p>Hello{' ' + user_name if user_name else ''},</p>
        <p>We received a request to reset your password.</p>
        <p>Click the link below to reset your password:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>
        <p>This link expires in 1 hour.</p>
        <p>If you didn't request this, please ignore this email.</p>
        """
        text_body = f"""
        Password Reset Request

        Hello{' ' + user_name if user_name else ''},

        We received a request to reset your password.

        Click the link below to reset your password:
        {reset_link}

        This link expires in 1 hour.

        If you didn't request this, please ignore this email.
        """

        return await self.send_email(
            to=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            reset_link=reset_link
        )

    def get_emails_to(self, email: str) -> List[MockEmail]:
        """Get all emails sent to a specific address."""
        return [e for e in self.sent_emails if e.to == email]

    def get_last_email(self) -> Optional[MockEmail]:
        """Get the last sent email."""
        return self.sent_emails[-1] if self.sent_emails else None

    def get_password_reset_emails(self) -> List[MockEmail]:
        """Get all password reset emails."""
        return [e for e in self.sent_emails if "reset" in e.subject.lower()]

    def reset(self):
        """Reset the mock state."""
        self.sent_emails = []
        self.send_count = 0

    def __len__(self) -> int:
        """Return the number of sent emails."""
        return len(self.sent_emails)
