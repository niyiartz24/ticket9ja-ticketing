import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv

load_dotenv()

def send_ticket_email(
    recipient_email,
    recipient_name,
    event_name,
    event_date,
    event_location,
    ticket_number,
    ticket_type,
    qr_code_base64,
    ticket_bg_image=None
):
    """
    Send ticket email with PDF attachment
    """
    
    email_host = os.getenv('EMAIL_HOST')
    email_port = int(os.getenv('EMAIL_PORT', 587))
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')
    email_from = os.getenv('EMAIL_FROM', 'SynthaxLab Ticketing <noreply@synthaxlab.com>')
    
    # Check if email is configured
    if not all([email_host, email_user, email_password]):
        print("⚠️ Email not configured - skipping")
        return False
    
    try:
        # Generate PDF ticket
        from pdf_generator import generate_ticket_pdf
        
        pdf_buffer = generate_ticket_pdf(
            ticket_number=ticket_number,
            recipient_name=recipient_name,
            event_name=event_name,
            event_date=event_date,
            event_location=event_location,
            ticket_type=ticket_type,
            qr_code_base64=qr_code_base64,
            ticket_bg_image=ticket_bg_image
        )
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = recipient_email
        msg['Subject'] = f'🎫 Your Ticket for {event_name}'
        
        # Email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .ticket-info {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }}
                .ticket-info p {{ margin: 10px 0; }}
                .footer {{ text-align: center; margin-top: 30px; color: #888; font-size: 12px; }}
                .btn {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎫 Your Ticket is Ready!</h1>
                </div>
                <div class="content">
                    <p>Hi {recipient_name},</p>
                    
                    <p>Your ticket for <strong>{event_name}</strong> has been issued!</p>
                    
                    <div class="ticket-info">
                        <p><strong>🎟️ Ticket Number:</strong> {ticket_number}</p>
                        <p><strong>🎫 Ticket Type:</strong> {ticket_type}</p>
                        <p><strong>📅 Event Date:</strong> {event_date}</p>
                        <p><strong>📍 Location:</strong> {event_location}</p>
                    </div>
                    
                    <p><strong>📎 Your ticket is attached as a PDF.</strong></p>
                    
                    <p>Please download and save the PDF ticket. You can either:</p>
                    <ul>
                        <li>Print the ticket and bring it to the event</li>
                        <li>Show the PDF on your phone at the entrance</li>
                    </ul>
                    
                    <p style="color: #d32f2f; font-weight: bold;">⚠️ Important: Do not share your ticket with anyone. Each ticket can only be used once.</p>
                    
                    <div class="footer">
                        <p>This is an automated email from SynthaxLab Ticketing System.</p>
                        <p>If you have any questions, please contact the event organizer.</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Attach PDF
        pdf_attachment = MIMEBase('application', 'pdf')
        pdf_attachment.set_payload(pdf_buffer.read())
        encoders.encode_base64(pdf_attachment)
        pdf_attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="{ticket_number}.pdf"'
        )
        msg.attach(pdf_attachment)
        
        # Send email
        print(f"📧 Connecting to {email_host}:{email_port}...")
        
        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(email_user, email_password)
            server.send_message(msg)
        
        print(f"✅ Email sent to {recipient_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email send failed: {e}")
        import traceback
        traceback.print_exc()
        return False
