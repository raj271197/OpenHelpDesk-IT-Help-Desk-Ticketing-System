import smtplib
from email.message import EmailMessage

from flask import current_app


def send_email(subject, message, recipient):
    if not recipient:
        return False

    username = current_app.config.get('MAIL_USERNAME')
    password = current_app.config.get('MAIL_PASSWORD')
    if not username or not password:
        return False

    try:
        email = EmailMessage()
        email['Subject'] = subject
        email['From'] = username
        email['To'] = recipient
        email.set_content(message)

        with smtplib.SMTP(
            current_app.config['MAIL_SERVER'],
            current_app.config['MAIL_PORT'],
            timeout=15,
        ) as smtp:
            if current_app.config['MAIL_USE_TLS']:
                smtp.starttls()
            smtp.login(username, password)
            smtp.send_message(email)
        return True
    except Exception:
        current_app.logger.exception('Failed to send email notification.')
        return False
