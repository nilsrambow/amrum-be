import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader


class CommunicationService:
    def __init__(self, email_config, templates_dir="templates"):
        self.email_config = email_config
        self.template_env = Environment(loader=FileSystemLoader(templates_dir))

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
