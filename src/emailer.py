import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List
import logging
from datetime import datetime
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobEmailer:
    def __init__(self, email_config_path: str = 'config/email_list.json'):
        """
        Initialize the job emailer with configuration.
        
        Args:
            email_config_path (str): Path to email configuration file
        """
        self.config = self._load_config(email_config_path)
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.sender_email = os.getenv('SENDER_EMAIL')

    def _load_config(self, config_path: str) -> Dict:
        """
        Load email configuration from JSON file.
        
        Args:
            config_path (str): Path to configuration file
        
        Returns:
            Dict: Email configuration
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading email config: {str(e)}")
            return {}

    def _create_html_table(self, jobs: List[Dict]) -> str:
        """
        Create HTML table from job listings.
        
        Args:
            jobs (List[Dict]): List of job listings
        
        Returns:
            str: HTML formatted table
        """
        df = pd.DataFrame(jobs)
        df = df[['title', 'company', 'location', 'url', 'match_score']]
        df = df.sort_values('match_score', ascending=False)
        
        # Convert DataFrame to HTML table with styling
        html_table = df.to_html(
            index=False,
            escape=False,
            formatters={
                'url': lambda x: f'<a href="{x}">Apply</a>',
                'match_score': lambda x: f'{x:.2f}'
            }
        )
        
        return html_table

    def _create_email_content(self, jobs: List[Dict], recipient_name: str) -> str:
        """
        Create HTML email content.
        
        Args:
            jobs (List[Dict]): List of job listings
            recipient_name (str): Name of the recipient
        
        Returns:
            str: HTML formatted email content
        """
        html_content = f"""
        <html>
            <head>
                <style>
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        margin: 20px 0;
                    }}
                    th, td {{
                        padding: 12px;
                        text-align: left;
                        border-bottom: 1px solid #ddd;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                    tr:hover {{
                        background-color: #f5f5f5;
                    }}
                    a {{
                        color: #0066cc;
                        text-decoration: none;
                    }}
                    a:hover {{
                        text-decoration: underline;
                    }}
                </style>
            </head>
            <body>
                <h2>Hello {recipient_name},</h2>
                <p>We found {len(jobs)} new job matches for you:</p>
                {self._create_html_table(jobs)}
                <p>Best regards,<br>Your Job Alert System</p>
            </body>
        </html>
        """
        return html_content

    def send_job_notifications(self, jobs: List[Dict]) -> bool:
        """
        Send email notifications for matching jobs.
        
        Args:
            jobs (List[Dict]): List of matching job listings
        
        Returns:
            bool: True if emails sent successfully, False otherwise
        """
        if not jobs and not self.config['email_settings']['send_empty_notifications']:
            logger.info("No jobs to send and empty notifications disabled")
            return True

        try:
            # Create SMTP connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)

            # Send to each recipient
            for recipient in self.config['recipients']:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = self.config['email_settings']['subject_template'].format(
                    new_matches=len(jobs)
                )
                msg['From'] = self.sender_email
                msg['To'] = recipient['email']

                html_content = self._create_email_content(jobs, recipient['name'])
                msg.attach(MIMEText(html_content, 'html'))

                server.send_message(msg)
                logger.info(f"Sent notification to {recipient['email']}")

            server.quit()
            return True

        except Exception as e:
            logger.error(f"Error sending email notifications: {str(e)}")
            return False

if __name__ == "__main__":
    # Test emailer
    emailer = JobEmailer()
    test_jobs = [
        {
            "title": "Data Scientist",
            "company": "Test Corp",
            "location": "New York, NY",
            "url": "http://example.com",
            "match_score": 0.95
        }
    ]
    emailer.send_job_notifications(test_jobs) 