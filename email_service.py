import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import os
import base64
import socket
from dotenv import load_dotenv

load_dotenv()

# Set socket timeout globally
socket.setdefaulttimeout(10)  # 10 second timeout

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
    """Send ticket email with embedded QR code - with timeout"""
    
    email_host = os.getenv('EMAIL_HOST')
    email_port = int(os.getenv('EMAIL_PORT', 587))
    email_user = os.getenv('EMAIL_USER')
    email_password = os.getenv('EMAIL_PASSWORD')
    email_from = os.getenv('EMAIL_FROM', 'SynthaxLab <noreply@synthaxlab.com>')
    
    if not all([email_host, email_user, email_password]):
        print("⚠️ Email not configured - missing credentials")
        return False
    
    try:
        # Decode QR code
        if 'base64,' in qr_code_base64:
            qr_data = qr_code_base64.split('base64,')[1]
        else:
            qr_data = qr_code_base64
        
        qr_bytes = base64.b64decode(qr_data)
        
        # Create email
        msg = MIMEMultipart('related')
        msg['From'] = email_from
        msg['To'] = recipient_email
        msg['Subject'] = f'🎫 Your Ticket for {event_name}'
        
        html_body = f"""
        <html>
        <body style="font-family: Arial; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1>🎫 Your Ticket is Ready!</h1>
            </div>
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px;">
                <p>Hi <strong>{recipient_name}</strong>,</p>
                
                <p>Your ticket for <strong>{event_name}</strong> has been issued!</p>
                
                <div style="background: white; padding: 30px; border-radius: 8px; margin: 20px 0; text-align: center; border: 2px solid #667eea;">
                    <h2 style="color: #667eea; margin-top: 0;">{event_name}</h2>
                    
                    <img src="cid:qrcode" alt="QR Code" style="max-width: 300px; margin: 20px 0;">
                    
                    <div style="text-align: left; margin: 20px 0;">
                        <p><strong>🎟️ Ticket:</strong> {ticket_number}</p>
                        <p><strong>🎫 Type:</strong> {ticket_type}</p>
                        <p><strong>📅 Date:</strong> {event_date}</p>
                        <p><strong>📍 Location:</strong> {event_location}</p>
                    </div>
                </div>
                
                <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; border-left: 4px solid #2196f3;">
                    <p style="margin: 0;"><strong>📱 How to use:</strong></p>
                    <ol style="margin: 10px 0;">
                        <li>Screenshot this email or save it</li>
                        <li>Show QR code at entrance</li>
                        <li>Staff will scan for entry</li>
                    </ol>
                </div>
                
                <div style="background: #ffebee; padding: 15px; border-radius: 5px; border-left: 4px solid #f44336; margin-top: 20px;">
                    <p style="margin: 0; color: #d32f2f;"><strong>⚠️ Important:</strong> Each ticket can only be used once. Do not share your QR code.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Attach QR image
        qr_image = MIMEImage(qr_bytes)
        qr_image.add_header('Content-ID', '<qrcode>')
        msg.attach(qr_image)
        
        # Send with timeout
        print(f"📧 Connecting to {email_host}:{email_port} (10s timeout)...")
        
        if email_port == 465:
            from smtplib import SMTP_SSL
            with SMTP_SSL(email_host, email_port, timeout=10) as server:
                server.login(email_user, email_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(email_host, email_port, timeout=10) as server:
                server.starttls()
                server.login(email_user, email_password)
                server.send_message(msg)
        
        print(f"✅ Email sent to {recipient_email}")
        return True
        
    except socket.timeout:
        print(f"❌ Email timeout - SMTP server not responding within 10 seconds")
        return False
    except smtplib.SMTPAuthenticationError:
        print(f"❌ Email authentication failed - check EMAIL_USER and EMAIL_PASSWORD")
        return False
    except Exception as e:
        print(f"❌ Email failed: {e}")
        import traceback
        traceback.print_exc()
        return False
