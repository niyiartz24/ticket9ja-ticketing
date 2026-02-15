import os
import base64
import requests
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
    """Send ticket email using SendGrid API with QR code as attachment"""
    
    api_key = os.getenv('SENDGRID_API_KEY')
    from_email = os.getenv('SENDGRID_FROM_EMAIL')
    from_name = os.getenv('SENDGRID_FROM_NAME', 'SynthaxLab')
    
    if not all([api_key, from_email]):
        print("⚠️ SendGrid not configured")
        return False
    
    try:
        # Clean base64 data
        if 'base64,' in qr_code_base64:
            qr_data = qr_code_base64.split('base64,')[1]
        else:
            qr_data = qr_code_base64
        
        # HTML email body
        html_content = f"""
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
                    
                    <img src="cid:qrcode" alt="QR Code" style="max-width: 300px; margin: 20px 0; display: block; margin-left: auto; margin-right: auto;">
                    
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
        
        # SendGrid API request with attachment
        url = "https://api.sendgrid.com/v3/mail/send"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "personalizations": [
                {
                    "to": [{"email": recipient_email, "name": recipient_name}],
                    "subject": f"🎫 Your Ticket for {event_name}"
                }
            ],
            "from": {
                "email": from_email,
                "name": from_name
            },
            "content": [
                {
                    "type": "text/html",
                    "value": html_content
                }
            ],
            "attachments": [
                {
                    "content": qr_data,
                    "type": "image/png",
                    "filename": "qrcode.png",
                    "disposition": "inline",
                    "content_id": "qrcode"
                }
            ]
        }
        
        print(f"📧 Sending email via SendGrid API to {recipient_email}...")
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 202:
            print(f"✅ Email sent successfully to {recipient_email}")
            return True
        else:
            print(f"❌ SendGrid API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
    except requests.exceptions.Timeout:
        print("❌ SendGrid API timeout")
        return False
    except Exception as e:
        print(f"❌ Email error: {e}")
        import traceback
        traceback.print_exc()
        return False
