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
    """Send ticket email with embedded QR code"""
    
    api_key = os.getenv('RESEND_API_KEY')
    from_email = os.getenv('EMAIL_FROM')
    
    print(f"\nSending ticket to: {recipient_email}")
    print(f"Ticket number: {ticket_number}")
    
    if not api_key or not from_email:
        print("ERROR: Email not configured")
        return False
    
    try:
        # Clean base64 data
        if 'base64,' in qr_code_base64:
            qr_data = qr_code_base64.split('base64,')[1]
        else:
            qr_data = qr_code_base64
        
        # Create ticket card HTML with cid reference
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                @media print {{
                    body {{ margin: 0; }}
                    .no-print {{ display: none; }}
                }}
            </style>
        </head>
        <body style="margin: 0; padding: 0; background-color: #f5f5f5; font-family: 'Arial', sans-serif;">
            <div style="max-width: 650px; margin: 0 auto; padding: 20px;">
                
                <!-- Email Header -->
                <div class="no-print" style="text-align: center; padding: 20px 0;">
                    <h2 style="color: #333; margin: 0;">Your Ticket is Ready!</h2>
                    <p style="color: #666; margin: 10px 0;">Save this ticket or screenshot it for entry</p>
                </div>
                
                <!-- TICKET CARD -->
                <div id="ticket-card" style="background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.15); margin: 20px 0;">
                    
                    <!-- Ticket Header -->
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; position: relative;">
                        <div style="background: rgba(255,255,255,0.2); display: inline-block; padding: 8px 20px; border-radius: 20px; margin-bottom: 15px;">
                            <span style="color: white; font-size: 13px; font-weight: bold; letter-spacing: 1px;">ADMIT ONE</span>
                        </div>
                        <h1 style="color: white; margin: 0; font-size: 32px; font-weight: bold;">{event_name}</h1>
                        <p style="color: rgba(255,255,255,0.95); margin: 15px 0 0 0; font-size: 18px;">{event_date}</p>
                        <p style="color: rgba(255,255,255,0.9); margin: 5px 0 0 0; font-size: 16px;">📍 {event_location}</p>
                    </div>
                    
                    <!-- Ticket Body -->
                    <div style="padding: 40px 30px;">
                        
                        <!-- Ticket Number Badge -->
                        <div style="text-align: center; margin-bottom: 30px;">
                            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: inline-block; padding: 12px 30px; border-radius: 25px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
                                <p style="color: rgba(255,255,255,0.8); margin: 0; font-size: 12px; letter-spacing: 2px;">TICKET NUMBER</p>
                                <p style="color: white; margin: 5px 0 0 0; font-size: 24px; font-weight: bold; letter-spacing: 3px;">{ticket_number}</p>
                            </div>
                        </div>
                        <!-- QR Code - Using Content-ID -->
                        <div style="text-align: center; margin: 30px 0; padding: 30px 20px; background: #f9f9f9; border-radius: 15px; overflow: visible;">
                           <p style="color: #666; margin: 0 0 20px 0; font-size: 14px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">Scan at Entrance</p>
                        <div style="display: inline-block; padding: 15px; background: white; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
                           <img src="cid:qrcode" alt="Ticket QR Code" style="display: block; max-width: 220px; width: 100%; height: auto;">
                             </div>
</div>
                        
                        <!-- Ticket Details -->
                        <div style="margin: 30px 0; padding: 25px; background: #f9f9f9; border-radius: 15px;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr style="border-bottom: 2px solid #e0e0e0;">
                                    <td style="padding: 15px 0; color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Ticket Holder</td>
                                    <td style="padding: 15px 0; color: #333; font-weight: bold; font-size: 16px; text-align: right;">{recipient_name}</td>
                                </tr>
                                <tr style="border-bottom: 2px solid #e0e0e0;">
                                    <td style="padding: 15px 0; color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Ticket Type</td>
                                    <td style="padding: 15px 0; text-align: right;">
                                        <span style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 6px 15px; border-radius: 20px; font-size: 14px; font-weight: bold;">{ticket_type}</span>
                                    </td>
                                </tr>
                                <tr style="border-bottom: 2px solid #e0e0e0;">
                                    <td style="padding: 15px 0; color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Event Date</td>
                                    <td style="padding: 15px 0; color: #333; font-weight: bold; font-size: 15px; text-align: right;">{event_date}</td>
                                </tr>
                                <tr>
                                    <td style="padding: 15px 0; color: #888; font-size: 13px; text-transform: uppercase; letter-spacing: 1px;">Venue</td>
                                    <td style="padding: 15px 0; color: #333; font-weight: bold; font-size: 15px; text-align: right;">{event_location}</td>
                                </tr>
                            </table>
                        </div>
                        
                        <!-- Instructions -->
                        <div style="background: linear-gradient(to right, #e8f4fd, #fef3e8); padding: 20px; border-radius: 12px; border-left: 5px solid #667eea; margin: 25px 0;">
                            <p style="margin: 0 0 12px 0; color: #333; font-weight: bold; font-size: 15px;">📱 How to Use Your Ticket:</p>
                            <ol style="margin: 0; padding-left: 20px; color: #555; font-size: 14px; line-height: 1.8;">
                                <li><strong>Save this email</strong> or take a screenshot of this ticket</li>
                                <li><strong>Present the QR code</strong> at the venue entrance</li>
                                <li><strong>Staff will scan</strong> your unique QR code for entry</li>
                            </ol>
                        </div>
                        
                        <!-- Important Notice -->
                        <div style="background: #fff3e0; padding: 18px; border-radius: 12px; border-left: 5px solid #ff9800; margin: 20px 0;">
                            <p style="margin: 0; color: #e65100; font-size: 14px; line-height: 1.6;">
                                <strong>⚠️ Important:</strong> This ticket is valid for <strong>single entry only</strong>. Each ticket has a unique QR code and number. Do not share your QR code.
                            </p>
                        </div>
                        
                        <!-- Ticket Footer -->
                        <div style="text-align: center; margin-top: 30px; padding-top: 25px; border-top: 2px dashed #e0e0e0;">
                            <p style="color: #999; font-size: 12px; margin: 0;">Powered by Ticket9ja Event Management</p>
                            <p style="color: #ccc; font-size: 11px; margin: 8px 0 0 0;">This is your official event ticket</p>
                        </div>
                        
                    </div>
                    
                </div>
                
                <!-- Email Footer -->
                <div class="no-print" style="text-align: center; padding: 30px 20px; color: #888;">
                    <p style="font-size: 14px; margin: 0 0 10px 0;">💾 <strong>Save This Ticket:</strong> Screenshot or save this email</p>
                    <p style="font-size: 13px; margin: 0; line-height: 1.6;">
                        Each ticket has a unique number and QR code.<br>
                        If you received multiple tickets, each will be in a separate email.
                    </p>
                </div>
                
            </div>
        </body>
        </html>
        """
        
        url = "https://api.resend.com/emails"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Send with QR code as inline attachment
        data = {
            "from": from_email,
            "to": [recipient_email],
            "subject": f"🎫 Ticket {ticket_number} - {event_name}",
            "html": html_content,
            "attachments": [
                {
                    "filename": "qrcode.png",
                    "content": qr_data,
                    "content_id": "qrcode"
                }
            ]
        }
        
        print(f"Calling Resend API with QR attachment...")
        response = requests.post(url, json=data, headers=headers, timeout=15)
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code in [200, 201]:
            print(f"SUCCESS: Ticket sent to {recipient_email}")
            return True
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
            return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
