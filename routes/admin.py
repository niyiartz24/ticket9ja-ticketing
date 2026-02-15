from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database.db import execute_query
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(fn):
    """Decorator to ensure user has admin role"""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = execute_query('SELECT role FROM users WHERE id = %s', (user_id,))
        
        if not user or user[0]['role'] != 'admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        return fn(*args, **kwargs)
    return wrapper

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    """Get admin dashboard statistics"""
    
    stats = execute_query('''
        SELECT 
            (SELECT COUNT(*) FROM users WHERE role = 'user') as total_users,
            (SELECT COUNT(*) FROM events WHERE status = 'published') as active_events,
            (SELECT COUNT(*) FROM tickets) as total_tickets_sold,
            (SELECT COALESCE(SUM(purchase_price), 0) FROM tickets WHERE status != 'cancelled') as total_revenue
    ''')
    
    if stats:
        return jsonify({
            'success': True,
            'data': stats[0]
        }), 200
    
    return jsonify({'success': False, 'error': 'Stats not available'}), 500
