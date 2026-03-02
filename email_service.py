import os
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
    """Send ticket email using Resend API"""
    
    api_key = os.getenv('RESEND_API_KEY')
    from_email = os.getenv('EMAIL_FROM', 'Ticket9ja <onboarding@resend.dev>')
    
    if not api_key:
        print("Resend API key not configured")
        return False
    
    try:
        # Clean base64 data
        if 'base64,' in qr_code_base64:
            qr_data = qr_code_base64.split('base64,')[1]
        else:
            qr_data = qr_code_base64
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: Arial, sans-serif;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                
                <!-- Header -->
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; border-radius: 12px 12px 0 0;">
                    <h1 style="color: white; margin: 0; font-size: 28px;">Your Ticket is Ready!</h1>
                    <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">{event_name}</p>
                </div>
                
                <!-- Body -->
                <div style="background: white; padding: 40px 30px; border-radius: 0 0 12px 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                    
                    <p style="color: #333; font-size: 16px; line-height: 1.6;">Hello <strong>{recipient_name}</strong>,</p>
                    <p style="color: #555; font-size: 15px; line-height: 1.6;">Your ticket has been confirmed. Please find your QR code below and present it at the entrance.</p>
                    
                    <!-- Ticket Card -->
                    <div style="border: 2px solid #667eea; border-radius: 12px; padding: 30px; margin: 30px 0; text-align: center;">
                        <h2 style="color: #667eea; margin: 0 0 20px 0; font-size: 22px;">{event_name}</h2>
                        
                        <!-- QR Code -->
                        <img src="cid:qrcode" alt="Your Ticket QR Code" style="width: 250px; height: 250px; display: block; margin: 0 auto 25px auto;">
                        
                        <!-- Ticket Details -->
                        <div style="text-align: left; background: #f9f9f9; padding: 20px; border-radius: 8px;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr style="border-bottom: 1px solid #eee;">
                                    <td style="padding: 10px 0; color: #888; font-size: 14px; width: 40%;">Ticket Number</td>
                                    <td style="padding: 10px 0; color: #333; font-weight: bold; font-size: 14px;">{ticket_number}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #eee;">
                                    <td style="padding: 10px 0; color: #888; font-size: 14px;">Ticket Type</td>
                                    <td style="padding: 10px 0; color: #333; font-weight: bold; font-size: 14px;">{ticket_type}</td>
                                </tr>
                                <tr style="border-bottom: 1px solid #eee;">
                                    <td style="padding: 10px 0; color: #888; font-size: 14px;">Date</td>
                                    <td style="padding: 10px 0; color: #333; font-weight: bold; font-size: 14px;">{event_date}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 10px 0; color: #888; font-size: 14px;">Location</td>
                                    <td style="padding: 10px 0; color: #333; font-weight: bold; font-size: 14px;">{event_location}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                    
                    <!-- Instructions -->
                    <div style="background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0 0 10px 0; color: #1a73e8; font-weight: bold; font-size: 15px;">How to use your ticket:</p>
                        <ol style="margin: 0; padding-left: 20px; color: #555; font-size: 14px; line-height: 2;">
                            <li>Save this email or screenshot the QR code</li>
                            <li>Present the QR code at the venue entrance</li>
                            <li>Staff will scan your code for entry</li>
                        </ol>
                    </div>
                    
                    <!-- Warning -->
                    <div style="background: #fff3e0; padding: 15px 20px; border-radius: 8px; border-left: 4px solid #ff9800;">
                        <p style="margin: 0; color: #e65100; font-size: 14px;"><strong>Important:</strong> This ticket is valid for single use only. Do not share your QR code.</p>
                    </div>
                    
                    <!-- Footer -->
                    <p style="margin-top: 30px; color: #999; font-size: 13px; text-align: center; line-height: 1.6;">
                        This is an automated message from Ticket9ja.<br>
                        Please do not reply to this email.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Resend API request
        url = "https://api.resend.com/emails"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "from": from_email,
            "to": [recipient_email],
            "subject": f"Your Ticket for {event_name} - {ticket_number}",
            "html": html_content,
            "attachments": [
                {
                    "filename": "ticket-qrcode.png",
                    "content": qr_data,
                    "content_type": "image/png"
                }
            ]
        }
        
        print(f"Sending email via Resend to {recipient_email}...")
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Resend response: {response.status_code} - {response.text}")
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"Email sent successfully to {recipient_email}")
            return True
        else:
            print(f"Resend API error: {response.status_code} - {response.text}")
            return False
        
    except requests.exceptions.Timeout:
        print("Resend API timeout")
        return False
    except Exception as e:
        print(f"Email error: {e}")
        import traceback
        traceback.print_exc()
        return False
