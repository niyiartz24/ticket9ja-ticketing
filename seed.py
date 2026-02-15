import sys
import os

# Add backend directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

import bcrypt
from database.db import execute_query, init_db
from datetime import datetime, timedelta

def seed_database():
    """Seed the database with admin and scanner accounts"""
    print("🌱 Seeding database...")
    
    # Initialize database connection
    try:
        init_db()
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return
    
    # Hash password
    password_hash = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create admin user
    print("👤 Creating admin user...")
    try:
        admin = execute_query('''
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        ''', ('admin@ticket9ja.com', password_hash, 'Admin User', 'admin'))
        
        if admin:
            admin_id = admin[0]['id']
            print(f"   ✅ Admin created (ID: {admin_id})")
        else:
            admin_result = execute_query('SELECT id FROM users WHERE email = %s', ('admin@synthaxlab.com',))
            admin_id = admin_result[0]['id'] if admin_result else None
            print("   ℹ️  Admin already exists")
    except Exception as e:
        print(f"   ❌ Failed to create admin: {e}")
        admin_id = None
    
    # Create scanner user
    print("👤 Creating scanner user...")
    try:
        scanner = execute_query('''
            INSERT INTO users (email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING id
        ''', ('scanner@ticket9ja.com', password_hash, 'Scanner User', 'scanner'))
        
        if scanner:
            print(f"   ✅ Scanner created")
        else:
            print("   ℹ️  Scanner already exists")
    except Exception as e:
        print(f"   ❌ Failed to create scanner: {e}")
    
    # Create sample event (only if admin was created)
    if admin_id:
        print("🎉 Creating sample event...")
        try:
            event = execute_query('''
                INSERT INTO events (created_by, name, description, event_date, location, capacity, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                admin_id,
                'Tech Conference 2025',
                'Annual technology and innovation conference',
                datetime.now() + timedelta(days=30),
                'Convention Center, San Francisco, CA',
                5000,
                'active'
            ))
            
            if event:
                event_id = event[0]['id']
                print(f"   ✅ Event created (ID: {event_id})")
                
                # Create ticket types
                print("🎫 Creating ticket types...")
                ticket_types = [
                    ('Regular', 299.00, 3000, False, 'Standard conference access', '#3B82F6'),
                    ('VIP', 599.00, 500, False, 'VIP access with exclusive sessions', '#8B5CF6'),
                    ('VVIP', 999.00, 100, False, 'All-access premium pass', '#F59E0B'),
                    ('Student', 149.00, 400, False, 'Discounted student rate (ID required)', '#10B981'),
                ]
                
                for name, price, qty, is_custom, desc, color in ticket_types:
                    execute_query('''
                        INSERT INTO ticket_types (event_id, name, price, quantity, is_custom, description, color)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ''', (event_id, name, price, qty, is_custom, desc, color), fetch=False)
                
                print("   ✅ Ticket types created")
        except Exception as e:
            print(f"   ❌ Failed to create event: {e}")
    
    print("\n✨ Database seeded successfully!\n")
    print("=" * 60)
    print("📧 Login Accounts:")
    print("=" * 60)
    print("   Admin Dashboard:")
    print("   📧 Email:    admin@ticket9ja.com")
    print("   🔒 Password: password123")
    print("")
    print("   Scanner App:")
    print("   📧 Email:    scanner@ticket9ja.com")
    print("   🔒 Password: password123")
    print("=" * 60)
    print("\n🎉 Ready to use!")
    print("   - Admin Dashboard: http://localhost:3000")
    print("   - Scanner App:     http://localhost:3001")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    # Verify DATABASE_URL exists
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in .env file!")
        print("Make sure .env file exists in backend folder")
    else:
        seed_database()