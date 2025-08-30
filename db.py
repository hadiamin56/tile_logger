import sqlite3
from pathlib import Path

DB_PATH = Path("data/tiles.db")
DB_PATH.parent.mkdir(exist_ok=True)

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cursor = conn.cursor()
    
    # Create daily_log table with item_name + quantity
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS daily_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        item_name TEXT,
        quantity INTEGER,
        labour_charges REAL
    )
    ''')

    # Config table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,      -- e.g. "Tile", "Interlock"
    option_name TEXT NOT NULL,   -- e.g. "1x1", "2x2", "60mm", "80mm"
    value REAL,
    UNIQUE(category, option_name)
)
    ''')

    # Labour payments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS labour_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        amount REAL,
        purpose TEXT
    )
    ''')

    # Vendors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT,
        details TEXT
    )
    ''')
    # Vendor-Materials table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendor_materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        material_name TEXT,
        FOREIGN KEY(vendor_id) REFERENCES vendors(id)
    )
    ''')

    # Materials Procurement table
    cursor.execute('''
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
    ''')

    
    # Material payments table (linked to vendor_id)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS material_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        date TEXT,
        amount REAL,
        FOREIGN KEY (vendor_id) REFERENCES vendors(id)
    )
    ''')

    # #sale
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sale (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT,
        customer_phone_number TEXT,
        tile_type TEXT,
        quantity INTEGER,
        price_per_tile REAL,
        amount REAL,
        payment_mode TEXT,
        date TEXT
    )
    ''')

    # ---- Default config values ----
    default_configs = [
        ("General", "LOADING", 0.25),
        ("Tile", "1x1", 25),
        ("Tile", "2x2", 40),
        ("Interlock", "60mm", 20),
        ("Interlock", "80mm", 25),
        ("Pot", "Standard", 10)
    ]

    for category, option, value in default_configs:
        cursor.execute(
            "INSERT OR IGNORE INTO config (category, option_name, value) VALUES (?, ?, ?)",
            (category, option, value)
        )

    conn.commit()
    conn.close()

