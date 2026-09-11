#!/usr/bin/env python3
"""
Optional email wrapper for cron.

Secrets MUST come from the environment — never hardcode passwords in the repo.

  export SMTP_HOST=smtp.example.com
  export SMTP_PORT=465
  export SMTP_USER=...
  export SMTP_PASSWORD=...
  export MAIL_FROM=...
  export MAIL_TO=...

Usage: python3 email_wrapper.py <script> <subject>
"""
from __future__ import annotations

import os
import smtplib
import subprocess
import sys
from email.mime.text import MIMEText
from email.utils import formataddr


def send_email(subject: str, body: str) -> bool:
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", "465"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    mail_from = os.environ.get("MAIL_FROM", user)
    mail_to = os.environ.get("MAIL_TO", "")
    if not all([host, user, password, mail_from, mail_to]):
        print(
            "邮件未发送：缺少 SMTP_HOST/SMTP_USER/SMTP_PASSWORD/MAIL_FROM/MAIL_TO",
            file=sys.stderr,
        )
        return False
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = formataddr(["Monitor", mail_from])
    msg["To"] = formataddr(["User", mail_to])
    msg["Subject"] = subject
    try:
        with smtplib.SMTP_SSL(host, port, timeout=30) as s:
            s.login(user, password)
            s.sendmail(mail_from, [mail_to], msg.as_string())
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 email_wrapper.py <脚本路径> <邮件主题>")
        sys.exit(1)
    result = subprocess.run(
        ["python3", sys.argv[1]],
        capture_output=True,
        text=True,
        timeout=180,
    )
    output = (result.stdout or "") + (result.stderr or "")
    ok = send_email(sys.argv[2], output)
    sys.exit(0 if ok else 1)
