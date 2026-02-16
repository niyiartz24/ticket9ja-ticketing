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
                
                # Create default ticket types for each event
ticket_types_data = [
    # Event 1 ticket types
    ('Early bird', 50.00, 100, event1_id),
    ('Late bird', 80.00, 50, event1_id),
    ('VIP', 150.00, 30, event1_id),
    ('Table for 4', 300.00, 10, event1_id),
    ('Table for 8', 500.00, 5, event1_id),
    
    # Event 2 ticket types
    ('Early bird', 40.00, 150, event2_id),
    ('Late bird', 70.00, 75, event2_id),
    ('VIP', 120.00, 40, event2_id),
    ('Table for 4', 250.00, 15, event2_id),
    ('Table for 8', 450.00, 8, event2_id),
]

print("Creating ticket types...")
for name, price, quantity, event_id in ticket_types_data:
    cur.execute('''
        INSERT INTO ticket_types (event_id, name, price, quantity, quantity_issued)
        VALUES (%s, %s, %s, %s, 0)
    ''', (event_id, name, price, quantity))

print("✅ Ticket types created")

    
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
