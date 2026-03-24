"""
Gmail → Snowflake Ingestion Script
Fetches emails from Gmail API and loads into GMAIL_ANALYTICS.CORE tables.
Run locally: python gmail_to_snowflake.py
"""

import json
import os
import datetime
import pandas as pd
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import snowflake.connector
import base64
import email as email_lib
from email.utils import parseaddr

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"

# ── Update these with your Snowflake connection details ──
SNOWFLAKE_CONFIG = {
    "account":   "<your-account>",      # e.g. "xy12345.us-east-1"
    "user":      "<your-user>",
    "password":  "<your-password>",      # or use authenticator="externalbrowser"
    "warehouse": "COMPUTE_WH",
    "database":  "GMAIL_ANALYTICS",
    "schema":    "CORE",
}
MAX_EMAILS = 10  # change to fetch more


def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def parse_headers(headers_list):
    return {h["name"]: h["value"] for h in headers_list}


def get_header(headers, name, default=""):
    return headers.get(name, default)


def extract_email_address(header_value):
    _, addr = parseaddr(header_value)
    return addr.lower() if addr else header_value.lower()


def extract_display_name(header_value):
    name, _ = parseaddr(header_value)
    return name if name else header_value.split("@")[0]


def fetch_emails(service, max_results=10):
    results = service.users().messages().list(
        userId="me", maxResults=max_results
    ).execute()
    messages = results.get("messages", [])

    emails = []
    contacts = {}
    threads = {}
    attachments = []
    label_maps = []

    all_labels = {}
    labels_resp = service.users().labels().list(userId="me").execute()
    for lbl in labels_resp.get("labels", []):
        all_labels[lbl["id"]] = {
            "LABEL_ID": hash(lbl["id"]) % 100000,
            "LABEL_NAME": lbl["name"],
            "LABEL_TYPE": lbl.get("type", "user").lower(),
            "COLOR": json.dumps(lbl.get("color")) if lbl.get("color") else None,
            "VISIBILITY": lbl.get("labelListVisibility", "show"),
            "GMAIL_LABEL_ID": lbl["id"],
            "CREATED_AT": datetime.datetime.now().isoformat(),
        }

    contact_id_counter = 10000
    msg_id_counter = 10000
    att_id_counter = 10000

    def get_or_create_contact(email_addr, display_name=""):
        nonlocal contact_id_counter
        key = email_addr.lower()
        if key not in contacts:
            domain = key.split("@")[1] if "@" in key else ""
            personal_domains = ["gmail.com","yahoo.com","outlook.com","hotmail.com","icloud.com"]
            ctype = "personal" if domain in personal_domains else "business"
            contacts[key] = {
                "CONTACT_ID": contact_id_counter,
                "EMAIL": key,
                "DISPLAY_NAME": display_name or key.split("@")[0],
                "DOMAIN": domain,
                "CONTACT_TYPE": ctype,
                "IS_INTERNAL": False,
                "CREATED_AT": datetime.datetime.now().isoformat(),
                "UPDATED_AT": datetime.datetime.now().isoformat(),
            }
            contact_id_counter += 1
        return contacts[key]["CONTACT_ID"]

    for msg_stub in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_stub["id"], format="full"
        ).execute()

        headers = parse_headers(msg.get("payload", {}).get("headers", []))
        thread_id_gmail = msg.get("threadId", "")
        label_ids = msg.get("labelIds", [])
        snippet = msg.get("snippet", "")
        size_estimate = msg.get("sizeEstimate", 0)
        internal_date = msg.get("internalDate", "0")
        sent_at = datetime.datetime.fromtimestamp(int(internal_date) / 1000)

        from_header = get_header(headers, "From", "unknown@unknown.com")
        to_header = get_header(headers, "To", "")
        cc_header = get_header(headers, "Cc", "")
        subject = get_header(headers, "Subject", "(no subject)")

        sender_email = extract_email_address(from_header)
        sender_name = extract_display_name(from_header)
        sender_cid = get_or_create_contact(sender_email, sender_name)

        to_emails = [extract_email_address(t.strip()) for t in to_header.split(",") if t.strip()]
        cc_emails = [extract_email_address(c.strip()) for c in cc_header.split(",") if c.strip()]
        to_cids = [get_or_create_contact(e) for e in to_emails]
        cc_cids = [get_or_create_contact(e) for e in cc_emails]

        body_text = ""
        body_html = ""
        msg_attachments = []

        def extract_parts(payload):
            nonlocal body_text, body_html, msg_attachments
            mime = payload.get("mimeType", "")
            if payload.get("filename"):
                msg_attachments.append({
                    "filename": payload["filename"],
                    "mimeType": mime,
                    "size": payload.get("body", {}).get("size", 0),
                    "attachmentId": payload.get("body", {}).get("attachmentId", ""),
                })
            elif mime == "text/plain" and not body_text:
                data = payload.get("body", {}).get("data", "")
                if data:
                    body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            elif mime == "text/html" and not body_html:
                data = payload.get("body", {}).get("data", "")
                if data:
                    body_html = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
            for part in payload.get("parts", []):
                extract_parts(part)

        extract_parts(msg.get("payload", {}))

        if thread_id_gmail not in threads:
            threads[thread_id_gmail] = {
                "THREAD_ID": hash(thread_id_gmail) % 10000000,
                "SUBJECT": subject.replace("Re: ", "").replace("Fwd: ", ""),
                "CATEGORY": "personal",
                "STARTED_AT": sent_at.isoformat(),
                "LAST_MESSAGE_AT": sent_at.isoformat(),
                "MESSAGE_COUNT": 0,
                "IS_MUTED": False,
                "CREATED_AT": sent_at.isoformat(),
            }
        threads[thread_id_gmail]["MESSAGE_COUNT"] += 1
        if sent_at.isoformat() > threads[thread_id_gmail]["LAST_MESSAGE_AT"]:
            threads[thread_id_gmail]["LAST_MESSAGE_AT"] = sent_at.isoformat()

        is_read = "UNREAD" not in label_ids
        is_starred = "STARRED" in label_ids
        is_sent = "SENT" in label_ids
        is_trash = "TRASH" in label_ids
        is_spam = "SPAM" in label_ids

        category = "personal"
        if "CATEGORY_PROMOTIONS" in label_ids:
            category = "promotions"
        elif "CATEGORY_UPDATES" in label_ids:
            category = "alerts"
        elif "CATEGORY_SOCIAL" in label_ids:
            category = "personal"
        elif "CATEGORY_FORUMS" in label_ids:
            category = "support"

        has_att = len(msg_attachments) > 0
        for att in msg_attachments:
            attachments.append({
                "ATTACHMENT_ID": att_id_counter,
                "MESSAGE_ID": msg_id_counter,
                "FILENAME": att["filename"],
                "CONTENT_TYPE": att["mimeType"],
                "SIZE_BYTES": att["size"],
                "IS_INLINE": False,
                "GMAIL_ATTACHMENT_ID": att["attachmentId"],
                "CREATED_AT": sent_at.isoformat(),
            })
            att_id_counter += 1

        emails.append({
            "MESSAGE_ID": msg_id_counter,
            "THREAD_ID": threads[thread_id_gmail]["THREAD_ID"],
            "GMAIL_MESSAGE_ID": msg_stub["id"],
            "SENDER_CONTACT_ID": sender_cid,
            "TO_CONTACT_IDS": json.dumps(to_cids),
            "CC_CONTACT_IDS": json.dumps(cc_cids),
            "BCC_CONTACT_IDS": json.dumps([]),
            "SUBJECT": subject,
            "SNIPPET": snippet[:500],
            "BODY_TEXT": body_text,
            "BODY_HTML": body_html,
            "SENT_AT": sent_at.isoformat(),
            "RECEIVED_AT": sent_at.isoformat(),
            "IS_READ": is_read,
            "IS_STARRED": is_starred,
            "IS_DRAFT": "DRAFT" in label_ids,
            "IS_SENT": is_sent,
            "IS_TRASH": is_trash,
            "IS_SPAM": is_spam,
            "HAS_ATTACHMENTS": has_att,
            "CATEGORY": category,
            "IMPORTANCE": "high" if "IMPORTANT" in label_ids else "normal",
            "SPAM_SCORE": 0.9 if is_spam else 0.0,
            "IS_SUSPICIOUS": is_spam,
            "PHISHING_INDICATORS": None,
            "HEADERS": json.dumps(dict(list(headers.items())[:20])),
            "RAW_SIZE_BYTES": size_estimate,
            "GMAIL_HISTORY_ID": str(msg.get("historyId", "")),
            "CREATED_AT": sent_at.isoformat(),
            "UPDATED_AT": sent_at.isoformat(),
        })

        for lid in label_ids:
            if lid in all_labels:
                label_maps.append({
                    "MESSAGE_ID": msg_id_counter,
                    "LABEL_ID": all_labels[lid]["LABEL_ID"],
                    "APPLIED_AT": sent_at.isoformat(),
                })
        msg_id_counter += 1

    return {
        "contacts": list(contacts.values()),
        "threads": list(threads.values()),
        "messages": emails,
        "attachments": attachments,
        "labels": list(all_labels.values()),
        "label_maps": label_maps,
    }


def load_to_snowflake(data):
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cur = conn.cursor()
    try:
        for table, rows in [
            ("EMAIL_CONTACTS", data["contacts"]),
            ("EMAIL_LABELS", data["labels"]),
            ("EMAIL_THREADS", data["threads"]),
            ("EMAIL_MESSAGES", data["messages"]),
            ("EMAIL_ATTACHMENTS", data["attachments"]),
            ("EMAIL_MESSAGE_LABEL_MAP", data["label_maps"]),
        ]:
            if not rows:
                continue
            df = pd.DataFrame(rows)
            cols = ", ".join(df.columns)
            placeholders = ", ".join(["%s"] * len(df.columns))
            sql = f"INSERT INTO GMAIL_ANALYTICS.CORE.{table} ({cols}) SELECT {placeholders}"
            values = [tuple(None if pd.isna(v) else v for v in row) for row in df.values]
            cur.executemany(sql, values)
            print(f"  Loaded {len(values)} rows into {table}")

        conn.commit()
        print("\nAll data committed to Snowflake!")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("Authenticating with Gmail API...")
    service = get_gmail_service()

    print(f"Fetching last {MAX_EMAILS} emails...")
    data = fetch_emails(service, MAX_EMAILS)

    print(f"\nExtracted:")
    print(f"  {len(data['contacts'])} contacts")
    print(f"  {len(data['threads'])} threads")
    print(f"  {len(data['messages'])} messages")
    print(f"  {len(data['attachments'])} attachments")
    print(f"  {len(data['labels'])} labels")
    print(f"  {len(data['label_maps'])} label mappings")

    print("\nLoading into Snowflake...")
    load_to_snowflake(data)