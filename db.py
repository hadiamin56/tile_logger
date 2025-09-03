import sqlite3
from pathlib import Path

DB_PATH = Path("data/tiles.db")
DB_PATH.parent.mkdir(exist_ok=True)

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    # Drop daily_log if exists to avoid old structure conflicts

    # --- Labour payments table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS labour_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        amount REAL,
        purpose TEXT
    )
    """)

    # --- Vendors table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        details TEXT
    )
    """)

    # --- Vendor-Materials table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendor_materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        material_name TEXT,
        FOREIGN KEY(vendor_id) REFERENCES vendors(id)
    )
    """)

    # --- Materials Procurement table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        material_type TEXT,
        quantity INTEGER,
        unit TEXT,
        price_per_unit REAL,
        total_price REAL,
        vendor_id INTEGER,
        FOREIGN KEY(vendor_id) REFERENCES vendors(id)
    )
    """)

    # --- Material payments table ---
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS material_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        date TEXT,
        amount REAL,
        FOREIGN KEY(vendor_id) REFERENCES vendors(id)
    )
    """)

    # --- Sale table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id TEXT,
            customer_name TEXT,
            customer_phone_number TEXT,
            tile_type TEXT,
            quantity INTEGER,
            price_per_tile REAL,
            amount REAL,
            payment_mode TEXT,
            date TEXT
        )
    """)

    # Create daily_log table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        tile_type TEXT,
        interlock_subtype TEXT,
        interlock_size TEXT,
        color TEXT,
        quantity INTEGER,
        labour_charge REAL,
        log_date DATE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tile_stock (
        tile_type TEXT,
        interlock_subtype TEXT,
        interlock_size TEXT,
        color TEXT,
        available_qty INTEGER,
        PRIMARY KEY (tile_type, interlock_subtype, interlock_size, color)
    )
    """)


    conn.commit()
    conn.close()
    print("✅ tiles.db initialized with all tables.")
