import sqlite3

# Connect to your database
conn = sqlite3.connect("data/tiles.db")
cur = conn.cursor()

# Create the tile_stock table if it doesn't exist
cur.execute("""
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

# Optional: clear existing stock
cur.execute("DELETE FROM tile_stock")
conn.commit()

# Initialize stock from daily_log
cur.execute("""
INSERT INTO tile_stock (tile_type, interlock_subtype, interlock_size, color, available_qty)
SELECT tile_type, interlock_subtype, interlock_size, color, SUM(quantity)
FROM daily_log
WHERE category='Tile'
GROUP BY tile_type, interlock_subtype, interlock_size, color
""")
conn.commit()

print("✅ tile_stock initialized from daily_log")

conn.close()
