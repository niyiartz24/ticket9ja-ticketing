from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import base64
from PIL import Image

def generate_ticket_pdf(
    ticket_number,
    recipient_name,
    event_name,
    event_date,
    event_location,
    ticket_type,
    qr_code_base64,
    ticket_bg_image=None
):
    """
    Generate a PDF ticket with optional custom background
    
    Returns: BytesIO buffer containing PDF
    """
    
    # Create PDF buffer
    buffer = BytesIO()
    
    # Create canvas (A4 size)
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    try:
        # Add background image if provided
        if ticket_bg_image:
            try:
                # Decode base64 background image
                if 'base64,' in ticket_bg_image:
                    bg_data = ticket_bg_image.split('base64,')[1]
                else:
                    bg_data = ticket_bg_image
                
                bg_bytes = base64.b64decode(bg_data)
                bg_img = Image.open(BytesIO(bg_bytes))
                
                # Convert to RGB if necessary
                if bg_img.mode != 'RGB':
                    bg_img = bg_img.convert('RGB')
                
                # Save to buffer for reportlab
                bg_buffer = BytesIO()
                bg_img.save(bg_buffer, format='JPEG')
                bg_buffer.seek(0)
                
                # Draw background to fill entire page
                c.drawImage(ImageReader(bg_buffer), 0, 0, width=width, height=height)
                
            except Exception as e:
                print(f"⚠️ Background image error: {e}")
                # Continue without background
                c.setFillColorRGB(0.95, 0.95, 0.95)
                c.rect(0, 0, width, height, fill=1)
        else:
            # Default light gray background
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(0, 0, width, height, fill=1)
        
        # Add semi-transparent white overlay for readability
        c.setFillColorRGB(1, 1, 1, alpha=0.85)
        ticket_box_width = 400
        ticket_box_height = 550
        ticket_box_x = (width - ticket_box_width) / 2
        ticket_box_y = (height - ticket_box_height) / 2
        
        c.roundRect(ticket_box_x, ticket_box_y, ticket_box_width, ticket_box_height, 20, fill=1)
        
        # Add border
        c.setStrokeColorRGB(0.2, 0.2, 0.2)
        c.setLineWidth(2)
        c.roundRect(ticket_box_x, ticket_box_y, ticket_box_width, ticket_box_height, 20, fill=0)
        
        # Center X position
        center_x = width / 2
        
        # Current Y position (start from top of ticket box)
        y = ticket_box_y + ticket_box_height - 60
        
        # Header
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(center_x, y, "🎫 Ticket9ja")
        
        y -= 50
        
        # Event Name
        c.setFont("Helvetica-Bold", 20)
        c.drawCentredString(center_x, y, event_name)
        
        y -= 60
        
        # QR Code
        try:
            # Decode base64 QR code
            if 'base64,' in qr_code_base64:
                qr_data = qr_code_base64.split('base64,')[1]
            else:
                qr_data = qr_code_base64
            
            qr_bytes = base64.b64decode(qr_data)
            qr_img = Image.open(BytesIO(qr_bytes))
            
            # Save to buffer
            qr_buffer = BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            # Draw QR code (centered)
            qr_size = 200
            qr_x = (width - qr_size) / 2
            c.drawImage(ImageReader(qr_buffer), qr_x, y - qr_size, width=qr_size, height=qr_size)
            
            y -= qr_size + 40
            
        except Exception as e:
            print(f"⚠️ QR code error: {e}")
            y -= 40
        
        # Ticket Number
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(center_x, y, ticket_number)
        
        y -= 40
        
        # Recipient Name
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(center_x, y, recipient_name)
        
        y -= 30
        
        # Ticket Type
        c.setFont("Helvetica", 14)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.drawCentredString(center_x, y, f"Ticket Type: {ticket_type}")
        
        y -= 40
        
        # Event Details
        c.setFont("Helvetica", 12)
        c.drawCentredString(center_x, y, f"📅 {event_date}")
        
        y -= 25
        
        c.drawCentredString(center_x, y, f"📍 {event_location}")
        
        y -= 40
        
        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(center_x, y, "Please present this ticket at the event entrance")
        
        # Finalize PDF
        c.save()
        
        # Get PDF data
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        print(f"❌ PDF generation error: {e}")
        import traceback
        traceback.print_exc()
        raise
