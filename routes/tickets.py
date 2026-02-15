from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import execute_query, get_db_connection, release_db_connection
from functools import wraps
import uuid
import qrcode
import io
import base64
from email_service import send_ticket_email
from psycopg2.extras import RealDictCursor

tickets_bp = Blueprint('tickets', __name__)

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = execute_query('SELECT role FROM users WHERE id = %s', (user_id,))
        
        if not user or user[0]['role'] != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

? = ticket_type['id']
            ticket_type_name = ticket_type['name']
            print(f"✅ Custom ticket type created: {ticket_type_name} (ID: {ticket_type_id})")
            
        else:
            print(f"📋 Getting ticket type {ticket_type_id}...")
            cur.execute('SELECT * FROM ticket_types WHERE id = %s', (ticket_type_id,))
            ticket_type = cur.fetchone()
            
            if not ticket_type:
                print("❌ Ticket type not found")
                return jsonify({'success': False, 'error': 'Ticket type not found'}), 404
            
            ticket_type_name = ticket_type['name']
            print(f"✅ Ticket type found: {ticket_type_name}")
            
            # Update quantity
            cur.execute('''
                UPDATE ticket_types 
                SET quantity_issued = quantity_issued + 1 
                WHERE id = %s
            ''', (ticket_type_id,))
            print("✅ Quantity updated")
        
        # Generate ticket number and QR code
        ticket_number = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        qr_data = f"{ticket_number}|{event_id}|{recipient_email}"
        
        print(f"🎟️ Generated ticket number: {ticket_number}")
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        print("✅ QR code generated")
        
        # Insert ticket
        print("💾 Inserting ticket into database...")
        cur.execute('''
            INSERT INTO tickets (
                event_id, ticket_type_id, qr_code, ticket_number,
                recipient_name, recipient_email, recipient_phone,
                ticket_bg_image, status, created_by, email_sent
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active', %s, false)
            RETURNING id, ticket_number, created_at
        ''', (
            event_id, ticket_type_id, qr_data, ticket_number,
            recipient_name, recipient_email, recipient_phone,
            ticket_bg_image, user_id
        ))
        
        ticket = cur.fetchone()
        ticket_id = ticket['id']
        
        print(f"✅ Ticket inserted with ID: {ticket_id}")
        
        # CRITICAL: Explicit commit
        print("💾 Committing transaction...")
        conn.commit()
        print("✅ Transaction committed!")
        
        # Verify it was actually saved
        print("🔍 Verifying ticket in database...")
        cur.execute('SELECT id, ticket_number FROM tickets WHERE id = %s', (ticket_id,))
        verify = cur.fetchone()
        
        if verify:
            print(f"✅ VERIFIED: Ticket {verify['ticket_number']} exists in database!")
        else:
            print(f"❌ WARNING: Ticket {ticket_id} NOT found after commit!")
        
        # Close cursor
        cur.close()
        
        # Prepare response data
        ticket_data = {
            'id': ticket_id,
@tickets_bp.route('/create', methods=['POST'])
@admin_required
def create_ticket():
    """Create ticket and send email"""
    print("\n" + "="*60)
    print("🎫 TICKET CREATION REQUEST")
    print("="*60)
    
    user_id = get_jwt_identity()
    user_id = int(user_id)
    
    data = request.get_json()
    print(f"📦 Request data: {data}")
    
    event_id = data.get('eventId')
    ticket_type_id = data.get('ticketTypeId')
    recipient_name = data.get('recipientName')
    recipient_email = data.get('recipientEmail')
    recipient_phone = data.get('recipientPhone', '')
    ticket_bg_image = data.get('ticketBgImage')
    custom_ticket_type = data.get('customTicketType')
    
    if not all([event_id, recipient_name, recipient_email]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    # Import here
    import qrcode
    import io
    import base64
    import uuid
    
    conn = get_db_connection()
    conn.autocommit = False
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print(f"📋 Getting event {event_id}...")
        cur.execute('SELECT * FROM events WHERE id = %s', (event_id,))
        event = cur.fetchone()
        
        if not event:
            print("❌ Event not found")
            return jsonify({'success': False, 'error': 'Event not found'}), 404
        
        print(f"✅ Event found: {event['name']}")
        
        # Handle ticket type
        if custom_ticket_type:
            print(f"📝 Creating custom ticket type: {custom_ticket_type['name']}")
            cur.execute('''
                INSERT INTO ticket_types (event_id, name, price, quantity, is_custom, description)
                VALUES (%s, %s, 0, 1, true, %s)
                RETURNING id, name
            ''', (event_id, custom_ticket_type['name'], custom_ticket_type.get('description', '')))
            
            ticket_type = cur.fetchone()
            ticket_type_id = ticket_type['id']
            ticket_type_name = ticket_type['name']
            print(f"✅ Custom ticket type created: {ticket_type_name} (ID: {ticket_type_id})")
            
        else:
            print(f"📋 Getting ticket type {ticket_type_id}...")
            cur.execute('SELECT * FROM ticket_types WHERE id = %s', (ticket_type_id,))
            ticket_type = cur.fetchone()
            
            if not ticket_type:
                print("❌ Ticket type not found")
                return jsonify({'success': False, 'error': 'Ticket type not found'}), 404
            
            ticket_type_name = ticket_type['name']
            print(f"✅ Ticket type found: {ticket_type_name}")
            
            # Update quantity
            cur.execute('''
                UPDATE ticket_types 
                SET quantity_issued = quantity_issued + 1 
                WHERE id = %s
            ''', (ticket_type_id,))
            print("✅ Quantity updated")
        
        # Generate ticket number and QR code
        ticket_number = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        qr_data = f"{ticket_number}|{event_id}|{recipient_email}"
        
        print(f"🎟️ Generated ticket number: {ticket_number}")
        
        # Generate QR code - FIXED VERSION
        qr_img = qrcode.make(qr_data)
        buffer = io.BytesIO()
        qr_img.save(buffer)
        buffer.seek(0)
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        print("✅ QR code generated")
        
        # Insert ticket
        print("💾 Inserting ticket into database...")
        cur.execute('''
            INSERT INTO tickets (
                event_id, ticket_type_id, qr_code, ticket_number,
                recipient_name, recipient_email, recipient_phone,
                ticket_bg_image, status, created_by, email_sent
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active', %s, false)
            RETURNING id, ticket_number, created_at
        ''', (
            event_id, ticket_type_id, qr_data, ticket_number,
            recipient_name, recipient_email, recipient_phone,
            ticket_bg_image, user_id
        ))
        
        ticket = cur.fetchone()
        ticket_id = ticket['id']
        
        print(f"✅ Ticket inserted with ID: {ticket_id}")
        
        # Commit
        print("💾 Committing transaction...")
        conn.commit()
        print("✅ Transaction committed!")
        
        # Verify
        print("🔍 Verifying ticket in database...")
        cur.execute('SELECT id, ticket_number FROM tickets WHERE id = %s', (ticket_id,))
        verify = cur.fetchone()
        
        if verify:
            print(f"✅ VERIFIED: Ticket {verify['ticket_number']} exists in database!")
        else:
            print(f"❌ WARNING: Ticket {ticket_id} NOT found after commit!")
        
        cur.close()
        
        # Prepare response
        ticket_data = {
            'id': ticket_id,
            'ticketNumber': ticket_number,
            'recipientName': recipient_name,
            'recipientEmail': recipient_email,
            'ticketType': ticket_type_name,
            'eventName': event['name'],
            'createdAt': ticket['created_at'].isoformat()
        }
        
        print("="*60)
        print("✅ TICKET CREATED SUCCESSFULLY")
        print("="*60 + "\n")
        
        return jsonify({
            'success': True,
            'message': 'Ticket created successfully',
            'data': {'ticket': ticket_data}
        }), 201
        
    except Exception as e:
        print("\n" + "!"*60)
        print("❌ ERROR OCCURRED")
        print("!"*60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        print("!"*60 + "\n")
        
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        release_db_connection(conn)
        
@tickets_bp.route('/<int:ticket_id>', methods=['PUT'])
@admin_required
def update_ticket(ticket_id):
    """Update ticket details"""
    data = request.get_json()
    
    fields = []
    values = []
    
    if 'recipientName' in data:
        fields.append('recipient_name = %s')
        values.append(data['recipientName'])
    
    if 'recipientEmail' in data:
        fields.append('recipient_email = %s')
        values.append(data['recipientEmail'])
    
    if 'recipientPhone' in data:
        fields.append('recipient_phone = %s')
        values.append(data['recipientPhone'])
    
    if 'status' in data:
        fields.append('status = %s')
        values.append(data['status'])
    
    if not fields:
        return jsonify({'success': False, 'error': 'No fields to update'}), 400
    
    values.append(ticket_id)
    query = f"UPDATE tickets SET {', '.join(fields)} WHERE id = %s RETURNING *"
    
    updated = execute_query(query, tuple(values))
    
    return jsonify({
        'success': True,
        'message': 'Ticket updated successfully',
        'data': {'ticket': updated[0] if updated else None}
    }), 200

@tickets_bp.route('/<int:ticket_id>', methods=['DELETE'])
@admin_required
def cancel_ticket(ticket_id):
    """Delete ticket completely (even if used)"""
    conn = get_db_connection()
    conn.autocommit = False
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print(f"🗑️ Deleting ticket {ticket_id}...")
        
        # Get ticket details first
        cur.execute('SELECT ticket_number, status FROM tickets WHERE id = %s', (ticket_id,))
        ticket = cur.fetchone()
        
        if not ticket:
            return jsonify({'success': False, 'error': 'Ticket not found'}), 404
        
        # Delete check-ins first (if any)
        cur.execute('DELETE FROM check_ins WHERE ticket_id = %s', (ticket_id,))
        deleted_checkins = cur.rowcount
        
        if deleted_checkins > 0:
            print(f"  ✓ Deleted {deleted_checkins} check-in record(s)")
        
        # Delete the ticket
        cur.execute('DELETE FROM tickets WHERE id = %s', (ticket_id,))
        print(f"  ✓ Deleted ticket: {ticket['ticket_number']}")
        
        # Update ticket type quantity if not custom
        cur.execute('''
            UPDATE ticket_types 
            SET quantity_issued = GREATEST(0, quantity_issued - 1)
            WHERE id = (SELECT ticket_type_id FROM tickets WHERE id = %s)
            AND is_custom = false
        ''', (ticket_id,))
        
        # Commit changes
        conn.commit()
        cur.close()
        
        print(f"✅ Ticket {ticket_id} deleted successfully")
        
        return jsonify({
            'success': True,
            'message': f'Ticket {ticket["ticket_number"]} deleted successfully'
        }), 200
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Delete ticket error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        release_db_connection(conn)

@tickets_bp.route('/resend/<int:ticket_id>', methods=['POST'])
@admin_required
def resend_ticket(ticket_id):
    """Resend ticket email"""
    
    ticket = execute_query('''
        SELECT t.*, 
               e.name as event_name, 
               e.event_date, 
               e.location,
               e.banner_image,
               tt.name as ticket_type_name
        FROM tickets t
        JOIN events e ON t.event_id = e.id
        JOIN ticket_types tt ON t.ticket_type_id = tt.id
        WHERE t.id = %s
    ''', (ticket_id,))
    
    if not ticket:
        return jsonify({'success': False, 'error': 'Ticket not found'}), 404
    
    ticket = ticket[0]
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(ticket['qr_code'])
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    # Resend email
    email_sent = send_ticket_email(
        recipient_email=ticket['recipient_email'],
        recipient_name=ticket['recipient_name'],
        event_name=ticket['event_name'],
        event_date=str(ticket['event_date']),
        event_location=ticket['location'],
        ticket_number=ticket['ticket_number'],
        ticket_type=ticket['ticket_type_name'],
        qr_code_base64=qr_image_base64,
        ticket_bg_image=ticket['ticket_bg_image'] or ticket['banner_image']
    )
    
    if email_sent:
        execute_query(
            'UPDATE tickets SET email_sent = true WHERE id = %s',
            (ticket_id,),
            fetch=False
        )
    
    return jsonify({
        'success': True,
        'message': 'Ticket email resent successfully'
    }), 200

@tickets_bp.route('/event/<int:event_id>', methods=['GET'])
@admin_required
def get_event_tickets(event_id):
    """Get all tickets for an event"""
    
    tickets = execute_query('''
        SELECT t.*, 
               tt.name as ticket_type_name,
               c.check_in_time,
               u.full_name as scanner_name
        FROM tickets t
        JOIN ticket_types tt ON t.ticket_type_id = tt.id
        LEFT JOIN check_ins c ON t.id = c.ticket_id
        LEFT JOIN users u ON c.scanner_id = u.id
        WHERE t.event_id = %s
        ORDER BY t.created_at DESC
    ''', (event_id,))
    
    return jsonify({
        'success': True,
        'data': {
            'tickets': tickets or [],
            'total': len(tickets) if tickets else 0
        }
    }), 200
