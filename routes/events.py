from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import execute_query, get_db_connection, release_db_connection
from functools import wraps
from psycopg2.extras import RealDictCursor
import base64
import os

events_bp = Blueprint('events', __name__)

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user_id = int(user_id)  # ✅ Convert string back to integer
        
        user = execute_query('SELECT role FROM users WHERE id = %s', (user_id,))
        
        if not user or user[0]['role'] != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        return fn(*args, **kwargs)
    return wrapper


@events_bp.route('', methods=['GET'])
@jwt_required()
def get_all_events():
    """Get all events with statistics"""
    status = request.args.get('status')
    
    query = '''
        SELECT e.*,
               u.full_name as created_by_name,
               COUNT(DISTINCT t.id) as total_tickets_issued,
               COUNT(DISTINCT CASE WHEN t.status = 'used' THEN t.id END) as tickets_used,
               COUNT(DISTINCT CASE WHEN t.status = 'active' THEN t.id END) as tickets_active,
               COALESCE(SUM(tt.price), 0) as total_revenue
        FROM events e
        LEFT JOIN users u ON e.created_by = u.id
        LEFT JOIN tickets t ON e.id = t.event_id
        LEFT JOIN ticket_types tt ON t.ticket_type_id = tt.id
    '''
    params = ()
    
    if status:
        query += ' WHERE e.status = %s'
        params = (status,)
    
    query += ' GROUP BY e.id, u.full_name ORDER BY e.event_date DESC'
    
    events = execute_query(query, params)
    
    return jsonify({
        'success': True,
        'data': {'events': events or []}
    }), 200

@events_bp.route('/<int:event_id>', methods=['GET'])
@admin_required
def get_event_by_id(event_id):
    """Get event with detailed statistics"""
    event = execute_query('''
        SELECT e.*,
               u.full_name as created_by_name,
               COUNT(DISTINCT t.id) as total_tickets_issued,
               COUNT(DISTINCT CASE WHEN t.status = 'used' THEN t.id END) as tickets_used,
               COUNT(DISTINCT CASE WHEN t.status = 'active' THEN t.id END) as tickets_active,
               COUNT(DISTINCT CASE WHEN t.status = 'cancelled' THEN t.id END) as tickets_cancelled
        FROM events e
        LEFT JOIN users u ON e.created_by = u.id
        LEFT JOIN tickets t ON e.id = t.event_id
        WHERE e.id = %s
        GROUP BY e.id, u.full_name
    ''', (event_id,))
    
    if not event:
        return jsonify({'success': False, 'error': 'Event not found'}), 404
    
    event = event[0]
    
    # Get ticket types with stats
    ticket_types = execute_query('''
        SELECT tt.*,
               COALESCE(SUM(CASE WHEN t.status != 'cancelled' THEN tt.price ELSE 0 END), 0) as revenue
        FROM ticket_types tt
        LEFT JOIN tickets t ON tt.id = t.ticket_type_id
        WHERE tt.event_id = %s
        GROUP BY tt.id
        ORDER BY tt.price ASC
    ''', (event_id,))
    
    event['ticketTypes'] = ticket_types or []
    
    # Get recent tickets
    recent_tickets = execute_query('''
        SELECT t.*, tt.name as ticket_type_name
        FROM tickets t
        JOIN ticket_types tt ON t.ticket_type_id = tt.id
        WHERE t.event_id = %s
        ORDER BY t.created_at DESC
        LIMIT 10
    ''', (event_id,))
    
    event['recentTickets'] = recent_tickets or []
    
    return jsonify({'success': True, 'data': {'event': event}}), 200

@events_bp.route('', methods=['POST'])
@admin_required
def create_event():
    """Create new event with optional banner image"""
    from database.db import get_db_connection, release_db_connection
    from psycopg2.extras import RealDictCursor
    
    try:
        user_id = get_jwt_identity()
        user_id = int(user_id)
        
        data = request.get_json()
        
        name = data.get('name')
        description = data.get('description')
        banner_image = data.get('bannerImage')
        event_date = data.get('eventDate')
        location = data.get('location')
        capacity = data.get('capacity')
        
        if not all([name, event_date, location, capacity]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Use a single transaction for everything
        conn = get_db_connection()
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Create event
                print("💾 Creating event...")
                cur.execute('''
                    INSERT INTO events (created_by, name, description, banner_image, event_date, location, capacity, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'draft')
                    RETURNING *
                ''', (user_id, name, description, banner_image, event_date, location, int(capacity)))
                
                event = cur.fetchone()
                
                if not event:
                    raise Exception("Failed to create event")
                
                event_id = event['id']
                print(f"✅ Event created with ID: {event_id}")
                
                # Create default ticket types in the same transaction
                print("🎫 Creating ticket types...")
                # Create default ticket types with new names
default_ticket_types = [
    {'name': 'Early bird', 'price': 50.00, 'quantity': 100},
    {'name': 'Late bird', 'price': 80.00, 'quantity': 50},
    {'name': 'VIP', 'price': 150.00, 'quantity': 30},
    {'name': 'Table for 4', 'price': 300.00, 'quantity': 10},
    {'name': 'Table for 8', 'price': 500.00, 'quantity': 5},
]

for tt in default_ticket_types:
    execute_query('''
        INSERT INTO ticket_types (event_id, name, price, quantity, quantity_issued)
        VALUES (%s, %s, %s, %s, 0)
    ''', (event_id, tt['name'], tt['price'], tt['quantity']), fetch=False)
                
                # Commit the entire transaction
                conn.commit()
                print("✅ Transaction committed successfully")
                
                return jsonify({
                    'success': True,
                    'message': 'Event created successfully',
                    'data': {'event': dict(event)}
                }), 201
                
        except Exception as e:
            conn.rollback()
            print(f"❌ Transaction rolled back: {e}")
            raise e
        finally:
            release_db_connection(conn)
        
    except Exception as e:
        print(f"❌ Create event error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    
@events_bp.route('/<int:event_id>', methods=['PUT'])
@admin_required
def update_event(event_id):
    """Update event details"""
    data = request.get_json()
    
    # Check if event exists
    event = execute_query('SELECT id FROM events WHERE id = %s', (event_id,))
    if not event:
        return jsonify({'success': False, 'error': 'Event not found'}), 404
    
    # Build update query dynamically
    fields = []
    values = []
    
    if 'name' in data:
        fields.append('name = %s')
        values.append(data['name'])
    
    if 'description' in data:
        fields.append('description = %s')
        values.append(data['description'])
    
    if 'bannerImage' in data:
        fields.append('banner_image = %s')
        values.append(data['bannerImage'])
    
    if 'eventDate' in data:
        fields.append('event_date = %s')
        values.append(data['eventDate'])
    
    if 'location' in data:
        fields.append('location = %s')
        values.append(data['location'])
    
    if 'capacity' in data:
        fields.append('capacity = %s')
        values.append(data['capacity'])
    
    if not fields:
        return jsonify({'success': False, 'error': 'No fields to update'}), 400
    
    values.append(event_id)
    query = f"UPDATE events SET {', '.join(fields)} WHERE id = %s RETURNING *"
    
    updated_event = execute_query(query, tuple(values))
    
    return jsonify({
        'success': True,
        'message': 'Event updated successfully',
        'data': {'event': updated_event[0] if updated_event else None}
    }), 200

@events_bp.route('/<int:event_id>', methods=['DELETE'])
@admin_required
def delete_event(event_id):
    """Delete event and all related data"""
    conn = get_db_connection()
    conn.autocommit = False
    
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        print(f"🗑️ Deleting event {event_id}...")
        
        # Get event details first
        cur.execute('SELECT name FROM events WHERE id = %s', (event_id,))
        event = cur.fetchone()
        
        if not event:
            return jsonify({'success': False, 'error': 'Event not found'}), 404
        
        # Delete in correct order due to foreign keys
        
        # 1. Delete check-ins first
        cur.execute('DELETE FROM check_ins WHERE ticket_id IN (SELECT id FROM tickets WHERE event_id = %s)', (event_id,))
        deleted_checkins = cur.rowcount
        print(f"  ✓ Deleted {deleted_checkins} check-ins")
        
        # 2. Delete tickets
        cur.execute('DELETE FROM tickets WHERE event_id = %s', (event_id,))
        deleted_tickets = cur.rowcount
        print(f"  ✓ Deleted {deleted_tickets} tickets")
        
        # 3. Delete ticket types
        cur.execute('DELETE FROM ticket_types WHERE event_id = %s', (event_id,))
        deleted_types = cur.rowcount
        print(f"  ✓ Deleted {deleted_types} ticket types")
        
        # 4. Finally delete the event
        cur.execute('DELETE FROM events WHERE id = %s', (event_id,))
        print(f"  ✓ Deleted event: {event['name']}")
        
        # Commit all changes
        conn.commit()
        cur.close()
        
        print(f"✅ Event {event_id} and all related data deleted successfully")
        
        return jsonify({
            'success': True,
            'message': f'Event "{event["name"]}" and all related data deleted successfully',
            'deleted': {
                'checkins': deleted_checkins,
                'tickets': deleted_tickets,
                'ticketTypes': deleted_types
            }
        }), 200
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Delete event error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
        
    finally:
        release_db_connection(conn)

@events_bp.route('/<int:event_id>/activate', methods=['POST'])
@admin_required
def activate_event(event_id):
    """Activate event"""
    execute_query(
        'UPDATE events SET status = %s WHERE id = %s',
        ('active', event_id),
        fetch=False
    )
    
    return jsonify({
        'success': True,
        'message': 'Event activated successfully'
    }), 200

@events_bp.route('/<int:event_id>/close', methods=['POST'])
@admin_required
def close_event(event_id):
    """Close event"""
    execute_query(
        'UPDATE events SET status = %s WHERE id = %s',
        ('closed', event_id),
        fetch=False
    )
    
    return jsonify({
        'success': True,
        'message': 'Event closed successfully'
    }), 200

@events_bp.route('/<int:event_id>/ticket-types', methods=['POST'])
@admin_required
def add_custom_ticket_type(event_id):
    """Add custom ticket type"""
    data = request.get_json()
    
    name = data.get('name')
    price = data.get('price', 0)
    quantity = data.get('quantity')
    description = data.get('description')
    color = data.get('color', '#3B82F6')
    
    if not all([name, quantity]):
        return jsonify({'success': False, 'error': 'Name and quantity required'}), 400
    
    ticket_type = execute_query('''
        INSERT INTO ticket_types (event_id, name, price, quantity, is_custom, description, color)
        VALUES (%s, %s, %s, %s, true, %s, %s)
        RETURNING *
    ''', (event_id, name, price, quantity, description, color))
    
    return jsonify({
        'success': True,
        'message': 'Custom ticket type created',
        'data': {'ticketType': ticket_type[0] if ticket_type else None}
    }), 201

@events_bp.route('/<int:event_id>/ticket-types/<int:type_id>', methods=['PUT'])
@admin_required
def update_ticket_type(event_id, type_id):
    """Update ticket type"""
    data = request.get_json()
    
    fields = []
    values = []
    
    if 'name' in data:
        fields.append('name = %s')
        values.append(data['name'])
    
    if 'price' in data:
        fields.append('price = %s')
        values.append(data['price'])
    
    if 'quantity' in data:
        fields.append('quantity = %s')
        values.append(data['quantity'])
    
    if 'description' in data:
        fields.append('description = %s')
        values.append(data['description'])
    
    if not fields:
        return jsonify({'success': False, 'error': 'No fields to update'}), 400
    
    values.extend([type_id, event_id])
    query = f"UPDATE ticket_types SET {', '.join(fields)} WHERE id = %s AND event_id = %s RETURNING *"
    
    updated = execute_query(query, tuple(values))
    
    return jsonify({
        'success': True,
        'message': 'Ticket type updated',
        'data': {'ticketType': updated[0] if updated else None}
    }), 200
