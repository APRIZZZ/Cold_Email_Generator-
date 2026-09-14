import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip()))


def send_email(to_address: str, subject: str, body: str) -> bool:
    """Sends an email via SMTP. If SMTP credentials aren't set in .env,
    it just prints the email instead -- handy for demos/testing."""
    if not SMTP_USER or not SMTP_PASSWORD:
        print("\n[SMTP not configured -- printing email instead of sending]")
        print(f"To: {to_address}\nSubject: {subject}\n\n{body}\n")
        return False

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_address
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_address, msg.as_string())
        return True
    except smtplib.SMTPException as e:
        print(f"Failed to send email: {e}")
        return False