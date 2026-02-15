from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import execute_query, get_db_connection, release_db_connection
from psycopg2.extras import RealDictCursor
from functools import wraps
from datetime import datetime

scanner_bp = Blueprint('scanner', __name__)

def scanner_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user_id = int(user_id)
        
        user = execute_query('SELECT role FROM users WHERE id = %s', (user_id,))
        
        if not user or user[0]['role'] not in ['scanner', 'admin']:
            return jsonify({'success': False, 'error': 'Scanner access required'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

@scanner_bp.route('/validate', methods=['POST'])
@scanner_required
def validate_ticket():
    """Validate a ticket by QR code"""
    user_id = get_jwt_identity()
    user_id = int(user_id)
    
    data = request.get_json()
    qr_code = data.get('qrCode')
    
    if not qr_code:
        return jsonify({'success': False, 'error': 'QR code required'}), 400
    
    print(f"🔍 Validating ticket: {qr_code}")
    
    conn = get_db_connection()
    conn.autocommit = False
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get ticket details
        cur.execute('''
            SELECT t.*, e.name as event_name, e.event_date, e.location,
                   tt.name as ticket_type_name
            FROM tickets t
            JOIN events e ON t.event_id = e.id
            JOIN ticket_types tt ON t.ticket_type_id = tt.id
            WHERE t.qr_code = %s
        ''', (qr_code,))
        
        ticket = cur.fetchone()
        
        if not ticket:
            print("❌ Ticket not found")
            return jsonify({
                'success': False,
                'error': 'Invalid ticket',
                'valid': False
            }), 404
        
        print(f"✅ Ticket found: {ticket['ticket_number']}")
        
        # Check if already used
        if ticket['status'] == 'used':
            print("⚠️ Ticket already used")
            
            # Get previous check-in details
            cur.execute('''
                SELECT check_in_time, u.full_name as scanner_name
                FROM check_ins ci
                JOIN users u ON ci.scanner_id = u.id
                WHERE ci.ticket_id = %s
                ORDER BY ci.check_in_time DESC
                LIMIT 1
            ''', (ticket['id'],))
            
            previous_checkin = cur.fetchone()
            
            return jsonify({
                'success': False,
                'error': 'Ticket already used',
                'valid': False,
                'ticket': {
                    'ticketNumber': ticket['ticket_number'],
                    'recipientName': ticket['recipient_name'],
                    'eventName': ticket['event_name'],
                    'ticketType': ticket['ticket_type_name'],
                    'status': ticket['status'],
                    'previousCheckIn': previous_checkin['check_in_time'].isoformat() if previous_checkin else None,
                    'scannedBy': previous_checkin['scanner_name'] if previous_checkin else None
                }
            }), 400
        
        # Check if cancelled
        if ticket['status'] == 'cancelled':
            print("❌ Ticket cancelled")
            return jsonify({
                'success': False,
                'error': 'Ticket has been cancelled',
                'valid': False
            }), 400
        
        # Mark as used
        print("✅ Marking ticket as used...")
        cur.execute('''
            UPDATE tickets
            SET status = 'used'
            WHERE id = %s
        ''', (ticket['id'],))
        
        # Record check-in
        cur.execute('''
            INSERT INTO check_ins (ticket_id, scanner_id)
            VALUES (%s, %s)
        ''', (ticket['id'], user_id))
        
        # Commit transaction
        conn.commit()
        print("✅ Check-in recorded")
        
        cur.close()
        
        return jsonify({
            'success': True,
            'valid': True,
            'message': 'Ticket validated successfully',
            'ticket': {
                'ticketNumber': ticket['ticket_number'],
                'recipientName': ticket['recipient_name'],
                'recipientEmail': ticket['recipient_email'],
                'eventName': ticket['event_name'],
                'eventDate': ticket['event_date'].isoformat(),
                'eventLocation': ticket['location'],
                'ticketType': ticket['ticket_type_name'],
                'checkInTime': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        release_db_connection(conn)

@scanner_bp.route('/history', methods=['GET'])
@scanner_required
def get_scan_history():
    """Get scanner's scan history"""
    user_id = get_jwt_identity()
    user_id = int(user_id)
    
    try:
        history = execute_query('''
            SELECT ci.*, t.ticket_number, t.recipient_name,
                   e.name as event_name, tt.name as ticket_type_name
            FROM check_ins ci
            JOIN tickets t ON ci.ticket_id = t.id
            JOIN events e ON t.event_id = e.id
            JOIN ticket_types tt ON t.ticket_type_id = tt.id
            WHERE ci.scanner_id = %s
            ORDER BY ci.check_in_time DESC
            LIMIT 50
        ''', (user_id,))
        
        return jsonify({
            'success': True,
            'data': {'history': history or []}
        }), 200
        
    except Exception as e:
        print(f"❌ History error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@scanner_bp.route('/stats', methods=['GET'])
@scanner_required
def get_scanner_stats():
    """Get scanner statistics"""
    user_id = get_jwt_identity()
    user_id = int(user_id)
    
    try:
        # Get total scans
        total = execute_query(
            'SELECT COUNT(*) as count FROM check_ins WHERE scanner_id = %s',
            (user_id,)
        )
        
        # Get today's scans
        today = execute_query('''
            SELECT COUNT(*) as count FROM check_ins
            WHERE scanner_id = %s AND DATE(check_in_time) = CURRENT_DATE
        ''', (user_id,))
        
        return jsonify({
            'success': True,
            'data': {
                'totalScans': total[0]['count'] if total else 0,
                'todayScans': today[0]['count'] if today else 0
            }
        }), 200
        
    except Exception as e:
        print(f"❌ Stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@scanner_bp.route('/lookup/<string:ticket_number>', methods=['GET'])
@scanner_required
def lookup_ticket(ticket_number):
    """Look up ticket by ticket number"""
    try:
        print(f"🔍 Looking up ticket: {ticket_number}")
        
        ticket = execute_query('''
            SELECT t.*, e.name as event_name
            FROM tickets t
            JOIN events e ON t.event_id = e.id
            WHERE t.ticket_number = %s
        ''', (ticket_number,))
        
        if not ticket:
            return jsonify({
                'success': False,
                'error': 'Ticket not found'
            }), 404
        
        return jsonify({
            'success': True,
            'ticket': ticket[0]
        }), 200
        
    except Exception as e:
        print(f"❌ Lookup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
