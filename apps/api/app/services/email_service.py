"""Email service for sending notifications and password reset links."""
import aiosmtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.settings import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Handle sending emails via SMTP."""

    @staticmethod
    async def send_password_reset_email(email: str, reset_token: str) -> bool:
        """
        Send password reset email with reset link.

        Args:
            email: User's email address
            reset_token: Password reset token

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Construct reset link
            reset_link = (
                f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
            )

            # Create email message
            subject = "Reset Your Veriply Password"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2>Password Reset Request</h2>
                        <p>We received a request to reset your password for your Veriply account.</p>
                        <p>Click the button below to reset your password. This link will expire in 1 hour.</p>
                        
                        <div style="margin: 30px 0;">
                            <a href="{reset_link}" style="background-color: #0ea5e9; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                                Reset Password
                            </a>
                        </div>
                        
                        <p>Or copy and paste this link in your browser:</p>
                        <p style="word-break: break-all; color: #0ea5e9;">
                            {reset_link}
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        
                        <p style="font-size: 12px; color: #999;">
                            If you didn't request a password reset, please ignore this email or contact support if you have concerns about your account security.
                        </p>
                        <p style="font-size: 12px; color: #999;">
                            This is an automated email. Please don't reply directly.
                        </p>
                    </div>
                </body>
            </html>
            """

            text_content = f"""
            Password Reset Request

            We received a request to reset your password for your Veriply account.

            Click the link below to reset your password (expires in 1 hour):
            {reset_link}

            If you didn't request this, please ignore this email.
            """

            return await EmailService._send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )

        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")
            return False

    @staticmethod
    async def send_password_reset_confirmation(email: str) -> bool:
        """
        Send confirmation email after password reset.

        Args:
            email: User's email address

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = "Your Veriply Password Has Been Reset"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2>Password Reset Successful</h2>
                        <p>Your password has been successfully reset.</p>
                        <p>You can now log in to your Veriply account with your new password.</p>
                        
                        <p style="margin: 30px 0;">
                            <a href="{settings.FRONTEND_URL}/login" style="background-color: #0ea5e9; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;">
                                Go to Login
                            </a>
                        </p>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        
                        <p style="font-size: 12px; color: #999;">
                            If you didn't reset your password, please contact support immediately as your account may be compromised.
                        </p>
                    </div>
                </body>
            </html>
            """

            text_content = """
            Password Reset Successful

            Your password has been successfully reset.
            You can now log in to your Veriply account with your new password.

            If you didn't reset your password, please contact support immediately.
            """

            return await EmailService._send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )

        except Exception as e:
            logger.error(
                f"Failed to send password reset confirmation to {email}: {str(e)}"
            )
            return False

    @staticmethod
    async def _send_email(
        to_email: str, subject: str, html_content: str, text_content: str
    ) -> bool:
        """
        Internal method to send email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Check configuration
            if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
                logger.warning(
                    "Email not configured. Set SMTP_USER and SMTP_PASSWORD in .env"
                )
                # For development, just log the email instead of failing
                logger.info(f"Email would be sent to {to_email}: {subject}")
                return True

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            
            # Set From with optional display name
            from_address = settings.EMAIL_FROM or settings.SMTP_USER
            if settings.EMAIL_DISPLAY_NAME:
                message["From"] = f"{settings.EMAIL_DISPLAY_NAME} <{from_address}>"
            else:
                message["From"] = from_address
            
            message["To"] = to_email
            
            # Add Reply-To if configured
            if settings.REPLY_TO:
                message["Reply-To"] = settings.REPLY_TO

            # Attach text and HTML parts
            message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))

            # Select TLS mode based on port (465 => implicit TLS, else STARTTLS)
            use_tls = int(getattr(settings, "SMTP_PORT", 587)) == 465
            start_tls = not use_tls

            async def _send_via_smtp():
                async with aiosmtplib.SMTP(
                    hostname=settings.SMTP_HOST,
                    port=settings.SMTP_PORT,
                    timeout=10,
                    use_tls=use_tls,
                    start_tls=start_tls,
                ) as smtp:
                    await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    await smtp.send_message(message)

            # Send with overall timeout guard (compatible with Python <3.11)
            await asyncio.wait_for(_send_via_smtp(), timeout=15)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except asyncio.TimeoutError:
            logger.error(f"Email timeout to {to_email} - check SMTP settings")
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    @staticmethod
    async def send_team_invite_email(email: str, invite_token: str) -> bool:
        """
        Send team invitation email with acceptance link.

        Args:
            email: Invitee email address
            invite_token: Token to accept the invitation

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            invite_link = f"{settings.FRONTEND_URL}/accept-invite?token={invite_token}"
            subject = "You’ve been invited to Veriply"
            html_content = f"""
            <html>
                <body style=\"font-family: Arial, sans-serif; line-height: 1.6; color: #333;\">
                    <div style=\"max-width: 600px; margin: 0 auto; padding: 20px;\">
                        <h2>Welcome to Veriply</h2>
                        <p>You’ve been invited to join a team on Veriply.</p>
                        <p>Click the button below to accept the invitation.</p>

                        <div style=\"margin: 30px 0;\">
                            <a href=\"{invite_link}\" style=\"background-color: #0ea5e9; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;\">
                                Accept Invitation
                            </a>
                        </div>

                        <p>Or copy and paste this link in your browser:</p>
                        <p style=\"word-break: break-all; color: #0ea5e9;\">
                            {invite_link}
                        </p>
                    </div>
                </body>
            </html>
            """

            text_content = f"""
            You’ve been invited to join a team on Veriply.

            Accept the invitation using this link:
            {invite_link}
            """

            return await EmailService._send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )
        except Exception as e:
            logger.error(f"Failed to send team invite email to {email}: {str(e)}")
            return False

    @staticmethod
    async def send_group_invite_email(email: str, invite_token: str, group_id: str) -> bool:
        """
        Send group invitation email with acceptance link.

        Args:
            email: Invitee email address
            invite_token: Signed JWT token containing group_id, user_id, and role
            group_id: ID of the group being invited to

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            invite_link = f"{settings.FRONTEND_URL}/accept-group-invite?token={invite_token}"
            subject = "You've been invited to join a group"
            html_content = f"""
            <html>
                <body style=\"font-family: Arial, sans-serif; line-height: 1.6; color: #333;\">
                    <div style=\"max-width: 600px; margin: 0 auto; padding: 20px;\">
                        <h2>Group Invitation</h2>
                        <p>You've been invited to join a group on Veriply.</p>
                        <p>Click the button below to accept the invitation.</p>

                        <div style=\"margin: 30px 0;\">
                            <a href=\"{invite_link}\" style=\"background-color: #0ea5e9; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; display: inline-block;\">
                                Accept Invitation
                            </a>
                        </div>

                        <p>Or copy and paste this link in your browser:</p>
                        <p style=\"word-break: break-all; color: #0ea5e9;\">
                            {invite_link}
                        </p>

                        <hr style=\"border: none; border-top: 1px solid #ddd; margin: 30px 0;\">

                        <p style=\"font-size: 12px; color: #999;\">
                            This invitation will expire in 48 hours.
                        </p>
                    </div>
                </body>
            </html>
            """

            text_content = f"""
            You've been invited to join a group on Veriply.

            Accept the invitation using this link:
            {invite_link}

            This invitation will expire in 48 hours.
            """

            return await EmailService._send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
            )

        except Exception as e:
            logger.error(f"Failed to send group invite email to {email}: {str(e)}")
            return False
