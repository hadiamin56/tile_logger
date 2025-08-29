import streamlit as st
from datetime import datetime
from db import get_conn
import pandas as pd

st.set_page_config(page_title="Tiles Loading", layout="wide")
st.title("🚚 Tiles Loading")

conn = get_conn()
cursor = conn.cursor()

# Fetch loading rate from config
cursor.execute("SELECT value FROM config WHERE name='loading'")
row = cursor.fetchone()
loading_rate = float(row[0]) if row else 0.25  # default

st.info(f"Current loading rate: **₹ {loading_rate} per tile**")

# --- Add new loading entry ---
with st.form("loading_form"):
    tiles_loaded = st.number_input("Number of tiles loaded", min_value=1, step=1)
    submit = st.form_submit_button("Save Loading")

    if submit:
        today = datetime.now().strftime("%Y-%m-%d")
        total_charge = tiles_loaded * loading_rate

        # Insert into daily_log
        cursor.execute("""
            INSERT INTO daily_log(date, item_name, quantity, labour_charges)
            VALUES (?, ?, ?, ?)
        """, (today, "loading", tiles_loaded, total_charge))

        conn.commit()
        st.success(f"✅ {tiles_loaded} tiles saved. ₹ {total_charge:.2f} added to Labour charges!")

# --- Display recent loading entries ---
st.subheader("📋 Recent Loading Entries")
df_loading = pd.read_sql("""
    SELECT date, quantity as tiles_loaded, labour_charges
    FROM daily_log
    WHERE item_name='loading'
    ORDER BY date DESC
""", conn)

if not df_loading.empty:
    st.dataframe(df_loading, use_container_width=True)
else:
    st.info("No loading records yet.")

conn.close()
