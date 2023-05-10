from datetime import datetime
from email.message import EmailMessage
from enum import Enum, auto
from pprint import pprint
import smtplib
from os import environ
import sys
import traceback

class EmailReason(Enum):
    ClearTable = auto()
    UploadScores = auto()


REASON_SUBJECT = {
    EmailReason.ClearTable: "BCOE&M Score tables were reset",
    EmailReason.UploadScores: "BCOE&M Scores were uploaded",
}

REASON_BODY = {
    EmailReason.ClearTable: """
Dear sir or madam,

The BCOE&M scores table has been reset.

Date: {date} UTC
Environment: {env_full_name}
User: {user_name} ({user_email})

Regards,


Score Upload System
""",
    EmailReason.UploadScores: """
Dear sir or madam,

Scores have been uploaded to the BCOE&M scores table.

Date: {date} UTC
Environment: {env_full_name}
User: {user_name} ({user_email})

Regards,


Score Upload System
"""
}

def send_audit_email(
    reason: EmailReason,
    env_full_name: str,
    user_name: str,
    user_email: str
    ) -> None:
    email_enabled = environ.get("EMAIL_ENABLED", "false") == "true"
    
    if not email_enabled:
        return
    
    try:
        email_from = environ['EMAIL_FROM']
        email_to = environ['AUTHORIZED_USERS']
        email_host = environ.get("EMAIL_HOST", 'localhost')
        email_port = int(environ.get("EMAIL_PORT", str(smtplib.SMTP_PORT)))

        print("sending audit email")
        msg = EmailMessage()
        msg['Subject'] = REASON_SUBJECT[reason]
        msg['From'] = email_from
        msg['Bcc'] = email_to
        msg.set_content(
            REASON_BODY[reason].format(
                date=datetime.utcnow(),
                env_full_name=env_full_name,
                user_email=user_email,
                user_name=user_name
            )
        )

        s = smtplib.SMTP(email_host, email_port)
        s.send_message(msg)
        s.quit()
    except Exception as e:
        pprint(e, stream=sys.stdout)
        traceback.print_exc()
