
from flask import Flask, jsonify, request, make_response
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os
from dotenv import load_dotenv

if os.getenv('RENDER') is None:
    load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

# Initialize JWT
jwt = JWTManager(app)

# Initialize database
from database.db import init_db
print("📡 Connecting to database...")
init_db()
print("✅ Database connected")

# MANUAL CORS - Add headers to every response
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

# Handle OPTIONS requests (preflight)
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = make_response('', 200)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response

# Import and register routes AFTER CORS setup
from routes.auth import auth_bp
from routes.events import events_bp
from routes.tickets import tickets_bp
from routes.scanner import scanner_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(events_bp, url_prefix='/api/events')
app.register_blueprint(tickets_bp, url_prefix='/api/tickets')
app.register_blueprint(scanner_bp, url_prefix='/api/scanner')

# Health check
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'cors': 'enabled (manual)'
    }), 200

@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({
        'name': 'SynthaxLab Ticketing API',
        'version': '1.0.0',
        'description': 'Admin + Scanner ticketing system'
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/admin/setup-database', methods=['POST'])
def setup_database():
    """One-time setup route - DELETE AFTER USE!"""
    try:
        # Run migrations
        from database.migrate import create_tables
        create_tables()
        
        # Seed database
        from database.db import execute_query
        import bcrypt
        
        # Create admin user
        admin_password = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        scanner_password = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        execute_query('''
            INSERT INTO users (email, password_hash, full_name, role, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (email) DO UPDATE SET 
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role
        ''', ('admin@ticket9ja.com', admin_password, 'Admin User', 'admin'), fetch=False)
        
        execute_query('''
            INSERT INTO users (email, password_hash, full_name, role, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON CONFLICT (email) DO UPDATE SET 
                password_hash = EXCLUDED.password_hash,
                role = EXCLUDED.role
        ''', ('scanner@ticket9ja.com', scanner_password, 'Scanner User', 'scanner'), fetch=False)
        
        return jsonify({
            'success': True,
            'message': 'Database setup completed!',
            'users': ['admin@ticket9ja.com', 'scanner@ticket9ja.com']
        }), 200
        
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    port = 5000
    
    print("\n" + "="*60)
    print("🚀 Ticket9ja Ticketing API")
    print("="*60)
    print(f"🔗 http://127.0.0.1:{port}")
    print(f"🔗 http://localhost:{port}")
    print("🌐 CORS: ENABLED (Manual Headers)")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True)
