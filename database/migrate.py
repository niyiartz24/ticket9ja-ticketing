import sys
import os

# Add backend directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from database.db import get_db_connection, release_db_connection, init_db

MIGRATIONS = [
    # Users table
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        full_name VARCHAR(200),
        role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'scanner')),
        is_active BOOLEAN DEFAULT true,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
    """,
    
    # Events table with banner image
    """
    CREATE TABLE IF NOT EXISTS events (
        id SERIAL PRIMARY KEY,
        created_by INTEGER NOT NULL REFERENCES users(id),
        name VARCHAR(255) NOT NULL,
        description TEXT,
        banner_image TEXT,
        event_date TIMESTAMP NOT NULL,
        location VARCHAR(500),
        capacity INTEGER,
        status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'closed')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
    CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
    """,
    
    # Ticket Types
    """
    CREATE TABLE IF NOT EXISTS ticket_types (
        id SERIAL PRIMARY KEY,
        event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
        name VARCHAR(100) NOT NULL,
        price DECIMAL(10, 2) NOT NULL DEFAULT 0,
        quantity INTEGER NOT NULL,
        quantity_issued INTEGER DEFAULT 0,
        is_custom BOOLEAN DEFAULT false,
        description TEXT,
        color VARCHAR(7),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT check_quantity_issued CHECK (quantity_issued <= quantity)
    );
    CREATE INDEX IF NOT EXISTS idx_ticket_types_event ON ticket_types(event_id);
    """,
    
    # Tickets with background image
    """
    CREATE TABLE IF NOT EXISTS tickets (
        id SERIAL PRIMARY KEY,
        event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
        ticket_type_id INTEGER NOT NULL REFERENCES ticket_types(id),
        qr_code VARCHAR(255) UNIQUE NOT NULL,
        ticket_number VARCHAR(50) UNIQUE NOT NULL,
        recipient_name VARCHAR(255) NOT NULL,
        recipient_email VARCHAR(255) NOT NULL,
        recipient_phone VARCHAR(20),
        ticket_bg_image TEXT,
        status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'used', 'cancelled')),
        email_sent BOOLEAN DEFAULT false,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER REFERENCES users(id)
    );
    CREATE INDEX IF NOT EXISTS idx_tickets_qr_code ON tickets(qr_code);
    CREATE INDEX IF NOT EXISTS idx_tickets_email ON tickets(recipient_email);
    CREATE INDEX IF NOT EXISTS idx_tickets_event ON tickets(event_id);
    """,
    
    # Check-ins
    """
    CREATE TABLE IF NOT EXISTS check_ins (
        id SERIAL PRIMARY KEY,
        ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
        scanner_id INTEGER NOT NULL REFERENCES users(id),
        check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        location VARCHAR(255)
    );
    CREATE INDEX IF NOT EXISTS idx_check_ins_ticket ON check_ins(ticket_id);
    CREATE INDEX IF NOT EXISTS idx_check_ins_scanner ON check_ins(scanner_id);
    """,
    
    # Updated_at trigger
    """
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ language 'plpgsql';

    DROP TRIGGER IF EXISTS update_events_updated_at ON events;
    CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

    DROP TRIGGER IF EXISTS update_tickets_updated_at ON tickets;
    CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """,
]

def run_migrations():
    """Run all migrations"""
    
    print("🔄 Starting migration process...")
    
    # Explicitly initialize database connection
    try:
        init_db()
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return
    
    conn = get_db_connection()
    
    try:
        print("🔄 Running migrations...")
        with conn.cursor() as cur:
            for i, migration in enumerate(MIGRATIONS, 1):
                print(f"📝 Migration {i}/{len(MIGRATIONS)}...")
                cur.execute(migration)
        conn.commit()
        print("\n✅ Migrations completed successfully!")
        print("📊 Tables created:")
        print("   - users")
        print("   - events")
        print("   - ticket_types")
        print("   - tickets")
        print("   - check_ins")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        release_db_connection(conn)

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if .env is loaded
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found!")
        print("Make sure .env file exists in backend folder")
        print("Expected format: DATABASE_URL=postgresql://user:pass@localhost:5432/dbname")
    else:
        print(f"✅ DATABASE_URL found: {database_url[:30]}...")
        run_migrations()
