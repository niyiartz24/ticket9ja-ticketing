from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import execute_query, get_db_connection, release_db_connection
from psycopg2.extras import RealDictCursor
from functools import wraps

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
    """Validate and check-in a ticket"""
    print("\n" + "="*60)
    print("TICKET VALIDATION REQUEST")
    print("="*60)
    
    user_id = get_jwt_identity()
    user_id = int(user_id)
    
    data = request.get_json()
    qr_code = data.get('qrCode')
    
    print(f"QR Code received: {qr_code}")
    print(f"Scanner ID: {user_id}")
    
    if not qr_code:
        return jsonify({'success': False, 'error': 'QR code required'}), 400
    
    conn = get_db_connection()
    conn.autocommit = False
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Find ticket by QR code
        print(f"Searching for ticket with QR: {qr_code}")
        
        cur.execute('''
            SELECT t.*, 
                   e.name as event_name,
                   tt.name as ticket_type
            FROM tickets t
            JOIN events e ON t.event_id = e.id
            JOIN ticket_types tt ON t.ticket_type_id = tt.id
            WHERE t.qr_code = %s
        ''', (qr_code,))
        
        ticket = cur.fetchone()
        
        if not ticket:
            print("Ticket not found!")
            return jsonify({
                'success': False,
                'error': 'Ticket not found. Please check the ticket number.'
            }), 404
        
        print(f"Ticket found: {ticket['ticket_number']} - Status: {ticket['status']}")
        
        # Check if ticket is active
        if ticket['status'] != 'active':
            print(f"Ticket status is {ticket['status']}, not active")
            return jsonify({
                'success': False,
                'error': f'Ticket is {ticket["status"]} and cannot be used'
            }), 400
        
        # Check if already checked in
        cur.execute('''
            SELECT c.*, u.full_name as scanner_name
            FROM check_ins c
            JOIN users u ON c.scanner_id = u.id
            WHERE c.ticket_id = %s
        ''', (ticket['id'],))
        
        existing_checkin = cur.fetchone()
        
        if existing_checkin:
            print("Ticket already checked in!")
            return jsonify({
                'success': False,
                'error': 'This ticket has already been used',
                'previous_checkin': {
                    'ticket_number': ticket['ticket_number'],
                    'recipient_name': ticket['recipient_name'],
                    'check_in_time': existing_checkin['check_in_time'].isoformat(),
                    'scanner_name': existing_checkin['scanner_name']
                }
            }), 400
        
        # Create check-in record
        print("Creating check-in record...")
        cur.execute('''
            INSERT INTO check_ins (ticket_id, scanner_id, check_in_time)
            VALUES (%s, %s, NOW())
            RETURNING check_in_time
        ''', (ticket['id'], user_id))
        
        checkin = cur.fetchone()
        
        # Update ticket status to used
        cur.execute('''
            UPDATE tickets 
            SET status = 'used' 
            WHERE id = %s
        ''', (ticket['id'],))
        
        conn.commit()
        cur.close()
        
        print("Check-in successful!")
        print("="*60 + "\n")
        
        return jsonify({
            'success': True,
            'message': 'Check-in successful!',
            'data': {
                'ticket_number': ticket['ticket_number'],
                'recipient_name': ticket['recipient_name'],
                'event_name': ticket['event_name'],
                'ticket_type': ticket['ticket_type'],
                'check_in_time': checkin['check_in_time'].isoformat()
            }
        }), 200
        
    except Exception as e:
        conn.rollback()
        print(f"Validation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        release_db_connection(conn)

@scanner_bp.route('/lookup/<ticket_number>', methods=['GET'])
@scanner_required
def lookup_ticket(ticket_number):
    """Lookup ticket by number for manual entry"""
    print(f"\nLookup request for ticket: {ticket_number}")
    
    try:
        ticket = execute_query('''
            SELECT t.*, 
                   e.name as event_name,
                   tt.name as ticket_type
            FROM tickets t
            JOIN events e ON t.event_id = e.id
            JOIN ticket_types tt ON t.ticket_type_id = tt.id
            WHERE t.ticket_number = %s
        ''', (ticket_number,))
        
        if not ticket:
            return jsonify({'success': False, 'error': 'Ticket not found'}), 404
        
        return jsonify({
            'success': True,
            'ticket': ticket[0]
        }), 200
        
    except Exception as e:
        print(f"Lookup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@scanner_bp.route('/stats', methods=['GET'])
@scanner_required
def get_stats():
    """Get scanner statistics"""
    user_id = get_jwt_identity()
    user_id = int(user_id)
    
    try:
        # Total scans
        total = execute_query('''
            SELECT COUNT(*) as count 
            FROM check_ins 
            WHERE scanner_id = %s
        ''', (user_id,))
        
        # Today's scans
        today = execute_query('''
            SELECT COUNT(*) as count 
            FROM check_ins 
            WHERE scanner_id = %s 
            AND DATE(check_in_time) = CURRENT_DATE
        ''', (user_id,))
        
        # Duplicate attempts (tickets that were already used)
        # This is an approximation - we can't track failed scans easily
        duplicates = 0
        
        return jsonify({
            'success': True,
            'data': {
                'total': total[0]['count'] if total else 0,
                'today': today[0]['count'] if today else 0,
                'duplicates': duplicates
            }
        }), 200
        
    except Exception as e:
        print(f"Stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
