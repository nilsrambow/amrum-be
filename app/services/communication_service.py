import logging
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html.parser import HTMLParser

from jinja2 import Environment, FileSystemLoader

from app.config.config import env

logger = logging.getLogger(__name__)


class _HtmlToText(HTMLParser):
    """Minimal HTML to plain text conversion for the text/plain alternative."""

    SKIP_TAGS = {"style", "title", "head", "script"}
    BLOCK_TAGS = {"p", "div", "h1", "h2", "h3", "h4", "ul", "ol", "table"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self._skip = 0
        self._href = None
        self._link = []
        self._cells = None
        self._in_thead = False

    def _sink(self):
        if self._href is not None:
            return self._link
        if self._cells:
            return self._cells[-1]
        return self.parts

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip += 1
        elif tag == "a":
            self._href = dict(attrs).get("href") or ""
            self._link = []
        elif tag == "br":
            self._sink().append("\n")
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag == "thead":
            self._in_thead = True
        elif tag == "tr":
            self._cells = []
        elif tag in ("td", "th"):
            if self._cells is not None:
                self._cells.append([])
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self._skip -= 1
        elif tag == "a":
            text = "".join(self._link).strip()
            href, self._href = self._href, None
            if not text or text == href:
                out = href
            else:
                out = f"{text} ({href})"
            self._sink().append(out)
        elif tag == "thead":
            self._in_thead = False
        elif tag == "tr":
            if self._cells is not None and not self._in_thead:
                cells = ["".join(c).strip() for c in self._cells]
                self.parts.append("\n" + ": ".join(c for c in cells if c) + "\n")
            self._cells = None
        elif tag in self.BLOCK_TAGS:
            self.parts.append("\n\n")

    def handle_data(self, data):
        if not self._skip:
            self._sink().append(re.sub(r"\s+", " ", data))

    def text(self) -> str:
        lines = [line.strip() for line in "".join(self.parts).split("\n")]
        return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"


def html_to_text(html: str) -> str:
    parser = _HtmlToText()
    parser.feed(html)
    return parser.text()


class CommunicationService:
    def __init__(self, email_config, templates_dir="templates", base_url=None):
        self.email_config = email_config
        self.template_env = Environment(loader=FileSystemLoader(templates_dir))
        self.base_url = base_url or os.getenv("FRONTEND_BASE_URL", "http://localhost:8080")

    def generate_magic_link(self, token: str) -> str:
        """Generate a magic link for guest access"""
        return f"{self.base_url}/#/guest/booking/{token}"

    def format_german_date(self, date_obj) -> str:
        """Format a date in German long form: Mo, 15. 07. 2024"""
        days = {0: 'Mo', 1: 'Di', 2: 'Mi', 3: 'Do', 4: 'Fr', 5: 'Sa', 6: 'So'}
        return f"{days[date_obj.weekday()]}, {date_obj.strftime('%d. %m. %Y')}"

    def send_booking_confirmation_email(self, booking, guest, token: str = None):
        """Send booking confirmation email with magic link"""
        context = {
            "guest_name": f"{guest.first_name} {guest.last_name}",
            "guest_first_name": guest.first_name,
            "check_in": booking.check_in.strftime("%Y-%m-%d"),
            "check_out": booking.check_out.strftime("%Y-%m-%d"),
            "check_in_formatted": self.format_german_date(booking.check_in),
            "check_out_formatted": self.format_german_date(booking.check_out),
            "booking_id": booking.id
        }

        if token:
            magic_link = self.generate_magic_link(token)
            context["magic_link"] = magic_link
            context["has_magic_link"] = True
        else:
            context["has_magic_link"] = False

        subject = f"Haus B: Terminbestätigung von {booking.check_in.strftime('%d. %m.')} bis {booking.check_out.strftime('%d. %m.')}"

        self.send_email(
            recipient=guest.email,
            subject=subject,
            template_name="bkg_confirmation_template",
            context=context
        )

    def send_booking_cancellation_email(self, booking, guest):
        """Send booking cancellation email to guest in German."""
        context = {
            "guest_name": f"{guest.first_name} {guest.last_name}",
            "guest_first_name": guest.first_name,
            "check_in": booking.check_in.strftime("%Y-%m-%d"),
            "check_out": booking.check_out.strftime("%Y-%m-%d"),
            "check_in_formatted": self.format_german_date(booking.check_in),
            "check_out_formatted": self.format_german_date(booking.check_out),
            "booking_id": booking.id,
        }

        subject = f"Haus B: Stornierung Deiner Buchung vom {booking.check_in.strftime('%d. %m.')} bis {booking.check_out.strftime('%d. %m.')}"

        self.send_email(
            recipient=guest.email,
            subject=subject,
            template_name="bkg_cancellation_template",
            context=context,
        )

    def send_email(self, recipient, subject, template_name, context):
        """Send an email using a template."""
        # Get the template
        template = self.template_env.get_template(f"{template_name}.html")

        # Render the template with context
        html_content = template.render(**context)

        # Create email message
        message = MIMEMultipart("alternative")
        message["From"] = self.email_config["sender"]
        message["To"] = recipient
        message["Cc"] = "hausb@mailbox.org"
        message["Subject"] = subject

        # Attach plain text first, HTML last - mail clients prefer the last alternative
        message.attach(MIMEText(html_to_text(html_content), "plain", "utf-8"))
        message.attach(MIMEText(html_content, "html", "utf-8"))

        # Check if real emails should be sent (defaults to False for safety)
        # Set SEND_REAL_EMAILS=true in .env file to actually send emails
        send_real_emails = os.getenv("SEND_REAL_EMAILS", "false").lower() == "true"
        if not send_real_emails:
            logger.info(
                "DEV MODE - email not sent | from=%s to=%s subject=%s body=%s",
                message["From"], message["To"], message["Subject"], html_content,
            )
            return True

        # Send email
        with smtplib.SMTP(
            self.email_config["smtp_server"], self.email_config["smtp_port"]
        ) as server:
            server.starttls()
            server.login(self.email_config["username"], self.email_config["password"])
            refused = server.send_message(message)
            if refused:
                logger.warning("Some recipients were refused by SMTP server: %s", refused)

        # Log the communication (could be expanded to database logging)
        self._log_communication(recipient, template_name, "email", "sent")
        return True

    def _log_communication(self, recipient, template_type, channel, status):
        """Log communication details."""
        logger.info("Communication sent: %s to %s via %s: %s", template_type, recipient, channel, status)
