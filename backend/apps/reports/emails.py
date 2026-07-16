"""Builds and sends the weekly HR report email — used both by the
Monday-morning scheduled cron and the on-demand "send to email" button.
"""
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from apps.reports.services import SUMMARY_LABELS
from apps.system_settings.email import get_configured_connection, get_from_email


def send_weekly_report_email(recipients, start, end, summary):
    """Returns False without sending anything if SMTP isn't configured yet
    (Settings -> Email Settings) — callers surface that to the user instead
    of silently doing nothing."""
    connection = get_configured_connection()
    if connection is None:
        return False

    link = f"{settings.FRONTEND_URL.rstrip('/')}/reports?week={start.isoformat()}"
    subject = f"Weekly HR Report — {start.strftime('%d %b')} to {end.strftime('%d %b %Y')}"

    rows = [(SUMMARY_LABELS[key], value) for key, value in summary.items() if key in SUMMARY_LABELS]

    text_lines = [f"Weekly HR Report: {start} to {end}", ""]
    text_lines += [f"{label}: {value}" for label, value in rows]
    text_lines += ["", f"View the full report and export to Excel/PDF: {link}"]
    text_body = "\n".join(text_lines)

    table_rows = "".join(
        f'<tr><td style="padding:6px 0;color:#475569;border-bottom:1px solid #f1f5f9;">{label}</td>'
        f'<td style="padding:6px 0;text-align:right;font-weight:600;color:#1f2937;'
        f'border-bottom:1px solid #f1f5f9;">{value}</td></tr>'
        for label, value in rows
    )
    html_body = f"""
    <div style="font-family:Arial,Helvetica,sans-serif;max-width:560px;margin:0 auto;">
      <h2 style="color:#1f2937;margin-bottom:2px;">Weekly HR Report</h2>
      <p style="color:#64748b;margin-top:0;">{start.strftime('%d %b')} &ndash; {end.strftime('%d %b %Y')}</p>
      <table style="width:100%;border-collapse:collapse;margin:16px 0;">{table_rows}</table>
      <a href="{link}"
         style="display:inline-block;background:#f2a900;color:#1f2937;font-weight:600;
                padding:10px 22px;border-radius:6px;text-decoration:none;">
        View Full Report
      </a>
    </div>
    """

    message = EmailMultiAlternatives(subject, text_body, get_from_email(), recipients, connection=connection)
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)
    return True
