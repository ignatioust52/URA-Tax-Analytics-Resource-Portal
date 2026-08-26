"""
email_utils.py — transactional email notifications for account lifecycle
events (registration, approval, rejection, status changes, password resets).

All sends are best-effort: a failed email NEVER blocks the underlying
account action. If SMTP isn't configured or fails, we log to Streamlit
and move on — the admin action (approve/reject/etc.) still succeeds.
"""

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import logging

logger = logging.getLogger(__name__)
URA_BLUE = "#1755a6"
URA_YELLOW = "#fff201"
URA_DARK = "#30302f"


def _smtp_configured():
    required = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"]
    return all(os.getenv(v) for v in required)


def _send_email(to_email, subject, html_body):
    """Low-level sender. Returns (success: bool, error_message: str)."""
    if not _smtp_configured():
        return False, "SMTP not configured — check .env"

    from_email = os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_USER"))
    from_name = os.getenv("SMTP_FROM_NAME", "URA Resource Portal")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as server:
            server.starttls(context=context)
            server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            server.sendmail(from_email, to_email, msg.as_string())
        return True, ""
    except Exception as e:
        return False, str(e)


def _wrap_template(title, intro_html, body_html, accent=URA_BLUE):
    """Shared HTML shell so every email looks consistent with the app theme."""
    return f"""
    <html>
      <body style="margin:0; padding:0; background-color:#F5F8FB; font-family: Arial, Helvetica, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="padding: 32px 0;">
          <tr>
            <td align="center">
              <table width="480" cellpadding="0" cellspacing="0"
                     style="background:#FFFFFF; border-radius:12px; overflow:hidden;
                            box-shadow:0 4px 16px rgba(13,46,99,0.08);">
                <tr>
                  <td style="background:{accent}; padding:20px 28px; border-bottom:4px solid {URA_YELLOW};">
                    <span style="color:#FFFFFF; font-size:18px; font-weight:700;">
                      URA Resource Portal
                    </span>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 28px;">
                    <h2 style="color:{URA_DARK}; margin:0 0 12px 0; font-size:20px;">{title}</h2>
                    <p style="color:#5A6B87; font-size:14px; line-height:1.5; margin:0 0 16px 0;">
                      {intro_html}
                    </p>
                    {body_html}
                  </td>
                </tr>
                <tr>
                  <td style="padding: 16px 28px; background:#F5F8FB;">
                    <p style="color:#8592A6; font-size:12px; margin:0;">
                      This is an automated message from the URA Resource Portal.
                      Please do not reply to this email.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """


def notify_registration_received(to_email):
    body = _wrap_template(
        title="✅ Account request received",
        intro_html=(
            "Thanks for creating an account. Your registration is now "
            "<b>pending administrator approval</b>. You'll receive another "
            "email as soon as it's been reviewed, and you'll be able to sign "
            "in once approved."
        ),
        body_html="",
    )
    ok, err = _send_email(to_email, "Your URA Resource Portal account is pending approval", body)
    if not ok:
        logger.warning(f"Registration email not sent to {to_email}: {err}")
    return ok


def notify_account_approved(to_email, role, departments):
    dept_line = ", ".join(departments) if departments else "All departments"
    body = _wrap_template(
        title="🎉 Your account has been approved",
        intro_html="Good news — an administrator has reviewed and approved your account.",
        body_html=f"""
            <table style="width:100%; border-collapse: collapse; margin-top: 8px;">
              <tr>
                <td style="padding:6px 0; color:#5A6B87; font-size:13px;">Role</td>
                <td style="padding:6px 0; color:{URA_DARK}; font-size:13px; font-weight:600; text-align:right;">{role.title()}</td>
              </tr>
              <tr>
                <td style="padding:6px 0; color:#5A6B87; font-size:13px;">Department access</td>
                <td style="padding:6px 0; color:{URA_DARK}; font-size:13px; font-weight:600; text-align:right;">{dept_line}</td>
              </tr>
            </table>
            <p style="color:#5A6B87; font-size:14px; margin-top:16px;">You can sign in now using the email and password you registered with.</p>
        """,
        accent=URA_BLUE,
    )
    ok, err = _send_email(to_email, "Your URA Resource Portal account has been approved", body)
    if not ok:
        logger.warning(f"Approval email not sent to {to_email}: {err}")
    return ok


def notify_account_rejected(to_email):
    body = _wrap_template(
        title="Account request declined",
        intro_html=(
            "An administrator has reviewed your registration request and it was "
            "not approved at this time. If you believe this is a mistake, please "
            "contact your department administrator."
        ),
        body_html="",
        accent=URA_DARK,
    )
    ok, err = _send_email(to_email, "Your URA Resource Portal account request was declined", body)
    if not ok:
        logger.warning(f"Rejection email not sent to {to_email}: {err}")
    return ok


def notify_account_status_changed(to_email, is_now_active):
    if is_now_active:
        title, intro, subject = (
            "✅ Your account has been re-enabled",
            "An administrator has re-enabled your account. You can sign in again using your existing credentials.",
            "Your URA Resource Portal account has been re-enabled",
        )
        accent = URA_BLUE
    else:
        title, intro, subject = (
            "🔒 Your account has been disabled",
            "An administrator has disabled your account. You will not be able to sign in until it's re-enabled. Contact your administrator if you have questions.",
            "Your URA Resource Portal account has been disabled",
        )
        accent = URA_DARK
    body = _wrap_template(title=title, intro_html=intro, body_html="", accent=accent)
    ok, err = _send_email(to_email, subject, body)
    if not ok:
        logger.warning(f"Status-change email not sent to {to_email}: {err}")
    return ok


def notify_password_reset(to_email, new_password):
    body = _wrap_template(
        title="🔑 Your password has been reset",
        intro_html="An administrator has reset your password. Please sign in with the temporary password below and change it as soon as possible.",
        body_html=f"""
            <div style="background:#F5F8FB; border-left:4px solid {URA_YELLOW}; border-radius:6px; padding:14px 18px; margin-top:8px;">
              <span style="color:#5A6B87; font-size:12px; text-transform:uppercase; letter-spacing:0.03em;">Temporary password</span><br/>
              <span style="color:{URA_DARK}; font-size:18px; font-weight:700; font-family: monospace;">{new_password}</span>
            </div>
        """,
    )
    ok, err = _send_email(to_email, "Your URA Resource Portal password has been reset", body)
    if not ok:
        logger.warning(f"Password reset email not sent to {to_email}: {err}")
    return ok


def notify_account_created_by_admin(to_email, temp_password, role, departments):
    dept_line = ", ".join(departments) if departments else "All departments"
    body = _wrap_template(
        title="👋 An account has been created for you",
        intro_html="An administrator has created a URA Resource Portal account on your behalf.",
        body_html=f"""
            <table style="width:100%; border-collapse: collapse; margin-top: 8px;">
              <tr>
                <td style="padding:6px 0; color:#5A6B87; font-size:13px;">Role</td>
                <td style="padding:6px 0; color:{URA_DARK}; font-size:13px; font-weight:600; text-align:right;">{role.title()}</td>
              </tr>
              <tr>
                <td style="padding:6px 0; color:#5A6B87; font-size:13px;">Department access</td>
                <td style="padding:6px 0; color:{URA_DARK}; font-size:13px; font-weight:600; text-align:right;">{dept_line}</td>
              </tr>
            </table>
            <div style="background:#F5F8FB; border-left:4px solid {URA_YELLOW}; border-radius:6px; padding:14px 18px; margin-top:16px;">
              <span style="color:#5A6B87; font-size:12px; text-transform:uppercase; letter-spacing:0.03em;">Temporary password</span><br/>
              <span style="color:{URA_DARK}; font-size:18px; font-weight:700; font-family: monospace;">{temp_password}</span>
            </div>
            <p style="color:#5A6B87; font-size:13px; margin-top:12px;">Please change this password after your first sign-in.</p>
        """,
    )
    ok, err = _send_email(to_email, "Your URA Resource Portal account is ready", body)
    if not ok:
        logger.warning(f"Welcome email not sent to {to_email}: {err}")
    return ok