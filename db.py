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
        name TEXT UNIQUE,
        value REAL
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

    # Materials Procurement table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        material_type TEXT,
        unit TEXT,
        price REAL,
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

    # Default config values
    cursor.execute("INSERT OR IGNORE INTO config(name, value) VALUES('TILE', 5)")
    cursor.execute("INSERT OR IGNORE INTO config(name, value) VALUES('POT', 10)")
    cursor.execute("INSERT OR IGNORE INTO config(name, value) VALUES('LOADING', 0.25)")
    cursor.execute("INSERT OR IGNORE INTO config(name, value) VALUES('1x1', 25)")


    conn.commit()
    conn.close()
