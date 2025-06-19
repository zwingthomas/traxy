# core/email.py
import os
import smtplib
from email.message import EmailMessage
import secrets_manager

SMTP_HOST = secrets_manager.get_secret("SMTP_HOST")
SMTP_PORT = "587"
SMTP_USER = secrets_manager.get_secret("SMTP_USER")
SMTP_PASS = secrets_manager.get_secret("SMTP_PASS")
WEB_BASE   = "https://www.traxy.app"
FROM_ADDR = "thomas@zwinger.us"

def send_reset_email(token: str, to_email: str):
    reset_link = f"{WEB_BASE}/reset-password?token={token}"
    msg = EmailMessage()
    msg["Subject"] = "Your password reset link"
    msg["From"]    = FROM_ADDR
    msg["To"]      = to_email
    msg.set_content(
        f"Click here to reset your password:\n\n{reset_link}\n\n"
        "If you didn’t ask, ignore this email."
    )
    msg.add_alternative(f"""
    <html>
      <body>
        <p>Click <a href="{reset_link}">this link</a> to reset your Traxy password.</p>
        <p>If you didn’t ask, you can safely ignore this message.</p>
      </body>
    </html>
    """, subtype="html")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)