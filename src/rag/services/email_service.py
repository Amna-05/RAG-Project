"""
Email service for sending emails via Resend.
File: src/rag/services/email_service.py

Handles:
- Password reset emails
- User notifications
- Welcome emails
"""
import logging
from typing import Optional
from rag.core.config import get_settings

logger = logging.getLogger(__name__)

# Try to import Resend, but make it optional
try:
    from resend import Resend
except ImportError:
    Resend = None


class EmailService:
    """Service for sending emails via Resend."""

    def __init__(self):
        """Initialize email service with API key."""
        settings = get_settings()
        self.api_key = settings.resend_api_key
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name

        if self.api_key and Resend:
            self.client = Resend(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("⚠️ Resend API key not configured. Email sending disabled.")

    def send_password_reset_email(
        self,
        email: str,
        reset_link: str,
        username: Optional[str] = None
    ) -> bool:
        """
        Send password reset email.

        Args:
            email: User's email address
            reset_link: Full URL to password reset page
            username: User's name (optional, for personalization)

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.client:
            logger.error("❌ Email service not available. Configure RESEND_API_KEY.")
            return False

        try:
            subject = "Reset Your Password"
            html_content = self._password_reset_template(reset_link, username)

            response = self.client.emails.send({
                "from": f"{self.from_name} <{self.from_email}>",
                "to": email,
                "subject": subject,
                "html": html_content
            })

            logger.info(
                f"✅ Password reset email sent",
                extra={"email": email, "response_id": response.get("id")}
            )
            return True

        except Exception as e:
            logger.error(
                f"❌ Failed to send password reset email: {str(e)}",
                extra={"email": email, "error": str(e)}
            )
            return False

    def send_welcome_email(self, email: str, username: str) -> bool:
        """
        Send welcome email to new user.

        Args:
            email: User's email address
            username: User's username

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.client:
            logger.warning("Email service not available. Skipping welcome email.")
            return False

        try:
            html_content = self._welcome_template(username)

            response = self.client.emails.send({
                "from": f"{self.from_name} <{self.from_email}>",
                "to": email,
                "subject": "Welcome to RAG!",
                "html": html_content
            })

            logger.info(f"✅ Welcome email sent to {email}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send welcome email: {str(e)}")
            return False

    @staticmethod
    def _password_reset_template(reset_link: str, username: Optional[str] = None) -> str:
        """Generate HTML template for password reset email."""
        name = username if username else "User"

        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Password Reset Request</h2>

                <p>Hi {name},</p>

                <p>We received a request to reset your password. Click the button below to set a new password:</p>

                <a href="{reset_link}" style="
                    display: inline-block;
                    background-color: #007bff;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                ">Reset Password</a>

                <p>Or copy this link: <code>{reset_link}</code></p>

                <p style="color: #666; font-size: 12px;">
                    This link will expire in 1 hour.<br>
                    If you didn't request this, you can ignore this email.
                </p>

                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                <p style="color: #999; font-size: 12px;">
                    RAG Application<br>
                    Questions? Reply to this email.
                </p>
            </body>
        </html>
        """

    @staticmethod
    def _welcome_template(username: str) -> str:
        """Generate HTML template for welcome email."""
        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Welcome to RAG! 🎉</h2>

                <p>Hi {username},</p>

                <p>Welcome to the RAG (Retrieval-Augmented Generation) application!</p>

                <p><strong>Here's what you can do:</strong></p>
                <ul>
                    <li>📄 Upload documents (PDF, DOCX, TXT, JSON)</li>
                    <li>🔍 Search using natural language (hybrid search)</li>
                    <li>🤖 Get AI-powered answers from your documents</li>
                    <li>💾 Save conversation history</li>
                </ul>

                <p><strong>Get started:</strong></p>
                <ol>
                    <li>Upload your first document</li>
                    <li>Wait for processing (usually <1 minute)</li>
                    <li>Ask questions in natural language</li>
                </ol>

                <p style="color: #666; font-size: 12px; margin-top: 30px;">
                    Happy exploring! If you have questions, reach out to us.
                </p>
            </body>
        </html>
        """


# Singleton instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service singleton."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service


async def send_password_reset_email(
    email: str,
    reset_link: str,
    username: Optional[str] = None
) -> bool:
    """Async wrapper for sending password reset email."""
    service = get_email_service()
    return service.send_password_reset_email(email, reset_link, username)


async def send_welcome_email(email: str, username: str) -> bool:
    """Async wrapper for sending welcome email."""
    service = get_email_service()
    return service.send_welcome_email(email, username)
