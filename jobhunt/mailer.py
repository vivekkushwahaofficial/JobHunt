"""Send the JobHunt digest over SMTP."""

from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage


def send(subject: str, html_body: str) -> None:
    # Read the SMTP server hostname from the environment.
    # For your Zoho India account: smtp.zoho.in
    host = os.getenv("SMTP_HOST", "smtp.zoho.in")

    # Zoho's account configuration shows port 465 with SSL.
    port = int(os.getenv("SMTP_PORT", "465"))

    # Email account used to authenticate and send the message.
    user = os.environ["SMTP_USER"]

    # App-specific password generated in Zoho.
    password = os.environ["SMTP_PASS"]

    # Destination email address.
    # Defaults to the sender's email if MAIL_TO is not configured.
    to_addr = os.getenv("MAIL_TO", user)

    # Create the email message.
    msg = EmailMessage()

    # Set the email subject.
    msg["Subject"] = subject

    # Set the sender.
    msg["From"] = user

    # Set the recipient.
    msg["To"] = to_addr

    # Add a plain-text fallback for email clients that do not support HTML.
    msg.set_content(
        "This digest is HTML. Open it in an HTML-capable email client."
    )

    # Add the HTML version of the email.
    msg.add_alternative(html_body, subtype="html")

    # Connect using implicit SSL.
    # Port 465 uses SSL from the beginning of the connection,
    # so we do NOT call starttls() here.
    with smtplib.SMTP_SSL(host, port, timeout=30) as s:
        # Authenticate with the Zoho account.
        s.login(user, password)

        # Send the email.
        s.send_message(msg)

    # Confirm that the message was handed to the SMTP server.
    print(f"  mailed -> {to_addr}")