import streamlit as st
import pandas as pd
from db import get_conn

st.set_page_config(page_title="Daily Tiles Log", layout="wide")
st.title("🧱 Daily Tiles Log")

# --- DB Connection ---
conn = get_conn()
cursor = conn.cursor()

# --- Fetch config ---
df_config = pd.read_sql("SELECT * FROM config", conn)

# Define main items
main_items = ["TILE", "LOADING", "POT"]

# --- Add new log ---
st.subheader("➕ Add New Daily Log")

selected_item = st.selectbox("Select Item", main_items)

if selected_item == "TILE":
    tile_type = st.selectbox("Tile Type", ["1x1", "INTERLOCK"])

    if tile_type == "1x1":
        # Fetch rate from config
        row = df_config[(df_config["category"] == "Tile") & (df_config["option_name"] == "1x1")]
        if not row.empty:
            unit_charge = row["value"].values[0]
            qty = st.number_input("Quantity Produced (1x1)", min_value=0, step=1)
            if st.button("Add 1x1 Log"):
                if qty > 0:
                    total = qty * unit_charge
                    cursor.execute(
                        "INSERT INTO daily_log(date, item_name, quantity, labour_charges) VALUES(CURRENT_DATE, ?, ?, ?)",
                        ("Tile 1x1", qty, total)
                    )
                    conn.commit()
                    st.success(f"✅ Added 1x1 | Qty {qty} | ₹{total:,.2f}")
        else:
            st.error("⚠️ No rate found in config for Tile 1x1")

    elif tile_type == "INTERLOCK":
        # Fetch available interlock sizes from config dynamically
        interlock_sizes = df_config[df_config["category"] == "Interlock"]

        if interlock_sizes.empty:
            st.warning("⚠️ No Interlock sizes found in config. Add them first.")
        else:
            st.write("### Enter Quantities for Interlock Sizes")
            size_qty_map = {}
            for _, row in interlock_sizes.iterrows():
                size = row["option_name"]
                rate = row["value"]
                qty = st.number_input(f"{size} (Rate ₹{rate})", min_value=0, step=1, key=f"qty_{size}")
                size_qty_map[size] = (qty, rate)

            if st.button("Add Interlock Logs"):
                any_added = False
                for size, (qty, rate) in size_qty_map.items():
                    if qty > 0:
                        total = qty * rate
                        cursor.execute(
                            "INSERT INTO daily_log(date, item_name, quantity, labour_charges) VALUES(CURRENT_DATE, ?, ?, ?)",
                            (f"Interlock {size}", qty, total)
                        )
                        any_added = True
                if any_added:
                    conn.commit()
                    st.success("✅ Interlock logs added successfully!")
                else:
                    st.info("No quantities entered.")

elif selected_item in ["LOADING", "POT"]:
    # Fetch rate from config
    row = df_config[df_config["category"].str.upper() == selected_item]
    if not row.empty:
        rate = row["value"].values[0]
        qty = st.number_input(f"Quantity for {selected_item}", min_value=0, step=1)
        if st.button(f"Add {selected_item} Log"):
            if qty > 0:
                total = qty * rate
                cursor.execute(
                    "INSERT INTO daily_log(date, item_name, quantity, labour_charges) VALUES(CURRENT_DATE, ?, ?, ?)",
                    (selected_item, qty, total)
                )
                conn.commit()
                st.success(f"✅ Added {selected_item} | Qty {qty} | ₹{total:,.2f}")
    else:
        st.error(f"⚠️ No rate found in config for {selected_item}")

st.markdown("---")

# --- Show Logs Table ---
st.subheader("📋 Daily Logs Table")
df_logs = pd.read_sql("SELECT * FROM daily_log ORDER BY date DESC", conn)
st.dataframe(df_logs, use_container_width=True)

conn.close()
