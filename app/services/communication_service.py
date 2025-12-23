import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader

from app.config.config import env


class CommunicationService:
    def __init__(self, email_config, templates_dir="templates", base_url="http://localhost:8080"):
        self.email_config = email_config
        self.template_env = Environment(loader=FileSystemLoader(templates_dir))
        self.base_url = base_url

    def generate_magic_link(self, token: str) -> str:
        """Generate a magic link for guest access"""
        return f"{self.base_url}/#/guest/booking/{token}"

    def send_booking_confirmation_email(self, booking, guest, token: str = None):
        """Send booking confirmation email with magic link"""
        
        # Format dates in German format without locale dependency
        def format_german_date(date_obj):
            """Format date in German format: Mo, 15. 07. 2024"""
            # German day abbreviations
            days = {
                0: 'Mo', 1: 'Di', 2: 'Mi', 3: 'Do', 4: 'Fr', 5: 'Sa', 6: 'So'
            }
            
            day_name = days[date_obj.weekday()]
            return f"{day_name}, {date_obj.strftime('%d. %m. %Y')}"
        
        context = {
            "guest_name": f"{guest.first_name} {guest.last_name}",
            "check_in": booking.check_in.strftime("%Y-%m-%d"),
            "check_out": booking.check_out.strftime("%Y-%m-%d"),
            "check_in_formatted": format_german_date(booking.check_in),
            "check_out_formatted": format_german_date(booking.check_out),
            "booking_id": booking.id
        }
        
        # Add magic link if token is provided
        if token:
            magic_link = self.generate_magic_link(token)
            context["magic_link"] = magic_link
            context["has_magic_link"] = True
        else:
            context["has_magic_link"] = False
        
        # Generate German subject line format
        subject = f"Haus B: Terminbestätigung von {booking.check_in.strftime('%d. %m.')} bis {booking.check_out.strftime('%d. %m.')}"
        
        self.send_email(
            recipient=guest.email,
            subject=subject,
            template_name="bkg_confirmation_template",
            context=context
        )

    def send_email(self, recipient, subject, template_name, context):
        """Send an email using a template."""
        # Get the template
        template = self.template_env.get_template(f"{template_name}.html")

        # Render the template with context
        html_content = template.render(**context)

        # Create email message
        message = MIMEMultipart()
        message["From"] = self.email_config["sender"]
        message["To"] = recipient
        message["Subject"] = subject

        # Attach HTML content
        message.attach(MIMEText(html_content, "html"))

        # print instead of send_message
        # if env == "development":
        #     print("\n----- DEV MODE: EMAIL NOT ACTUALLY SENT -----")
        #     print(f"From: {message['From']}")
        #     print(f"To: {message['To']}")
        #     print(f"Subject: {message['Subject']}")
        #     print(f"\nBody:\n{html_content}")
        #     print("-----------------------------------------\n")

        #     return True

        # Send email
        with smtplib.SMTP(
            self.email_config["smtp_server"], self.email_config["smtp_port"]
        ) as server:
            server.starttls()
            server.login(self.email_config["username"], self.email_config["password"])
            server.send_message(message)

        # Log the communication (could be expanded to database logging)
        self._log_communication(recipient, template_name, "email", "sent")

    def _log_communication(self, recipient, template_type, channel, status):
        """Log communication details."""
        # This could write to a database table in a full implementation
        print(
            f"Communication sent: {template_type} to {recipient} via {channel}: {status}"
        )
