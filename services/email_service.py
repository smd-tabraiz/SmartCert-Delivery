import csv
import os
import time
import base64
import re

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName, FileType, Disposition
)

# ======================================================
# EMAIL VALIDATION
# ======================================================

EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

ALLOWED_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "protonmail.com"
}

def is_valid_domain(email: str) -> bool:
    try:
        domain = email.split("@")[1].lower()
    except IndexError:
        return False

    if domain in ALLOWED_DOMAINS:
        return True

    if domain.endswith(".ac.in"):   # ✅ college emails
        return True

    return False


def clean_name(name: str) -> str:
    return name.strip().replace(" ", "_")


def send_certificates(
    csv_file: str,
    renamed_folder: str,
    sender_email: str,
    sendgrid_api_key: str,
    subject: str,
    email_body: str,
    log_file: str
):
    """
    RETURNS:
    sent_count, failed_count, failed_details
    """

    sent_count = 0
    failed_count = 0
    failed_details = []

    if not email_body or email_body.strip() == "":
        email_body = (
            "Dear {name},\n\n"
            "Thank you for participating in our event.\n"
            "Please find your certificate attached.\n\n"
            "Regards,\n"
            "Event Team"
        )

    # Init log
    with open(log_file, "w", encoding="utf-8") as log:
        log.write("Certificate Sending Logs (SendGrid API)\n\n")

    sg = SendGridAPIClient(sendgrid_api_key)

    # 🔥 SAFE CSV READ + HEADER NORMALIZATION
    with open(csv_file, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

        for row in reader:
            name = row.get("name", "").strip()
            email = row.get("email", "").strip()

            # ===============================
            # 1️⃣ EMAIL FORMAT
            # ===============================
            if not EMAIL_REGEX.match(email):
                failed_count += 1
                failed_details.append({
                    "name": name or "N/A",
                    "email": email or "N/A",
                    "certificate": "N/A",
                    "reason": "Invalid email format"
                })
                continue

            # ===============================
            # 2️⃣ DOMAIN CHECK
            # ===============================
            if not is_valid_domain(email):
                failed_count += 1
                failed_details.append({
                    "name": name,
                    "email": email,
                    "certificate": "N/A",
                    "reason": "Invalid email domain"
                })
                continue

            # ===============================
            # 3️⃣ CERTIFICATE CHECK
            # ===============================
            safe_name = clean_name(name)
            cert_file = None
            cert_filename = None

            for ext in [".jpg", ".jpeg", ".png", ".pdf"]:
                path = os.path.join(renamed_folder, safe_name + ext)
                if os.path.exists(path):
                    cert_file = path
                    cert_filename = safe_name + ext
                    break

            if not cert_file:
                failed_count += 1
                failed_details.append({
                    "name": name,
                    "email": email,
                    "certificate": "Not Found",
                    "reason": "Certificate missing"
                })
                continue

            # ===============================
            # 4️⃣ SEND EMAIL
            # ===============================
            personalized_body = email_body.replace("{name}", name)

            message = Mail(
                from_email=sender_email,
                to_emails=email,
                subject=subject,
                plain_text_content=personalized_body
            )

            with open(cert_file, "rb") as f:
                encoded = base64.b64encode(f.read()).decode()

            message.attachment = Attachment(
                FileContent(encoded),
                FileName(os.path.basename(cert_file)),
                FileType("application/octet-stream"),
                Disposition("attachment")
            )

            try:
                response = sg.send(message)

                if response.status_code == 202:
                    sent_count += 1
                else:
                    failed_count += 1
                    failed_details.append({
                        "name": name,
                        "email": email,
                        "certificate": cert_filename,
                        "reason": f"SendGrid rejected ({response.status_code})"
                    })

            except Exception as e:
                failed_count += 1
                failed_details.append({
                    "name": name,
                    "email": email,
                    "certificate": cert_filename,
                    "reason": str(e)
                })

            time.sleep(1)

    return sent_count, failed_count, failed_details
