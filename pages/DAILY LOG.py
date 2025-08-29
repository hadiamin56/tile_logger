import streamlit as st
import pandas as pd
from db import get_conn

st.set_page_config(page_title="Daily Tiles Log", layout="wide")
st.title("🧱 Daily Tiles Log")

conn = get_conn()
cursor = conn.cursor()

# Fetch config for dropdown items
df_config = pd.read_sql("SELECT * FROM config", conn)
items = [row['name'] for index, row in df_config.iterrows()]

# --- Add new log ---
st.subheader("➕ Add New Daily Log")
col1, col2, col3 = st.columns([2, 1, 2])

with col1:
    selected_item = st.selectbox("Select Item", items)
with col2:
    quantity = st.number_input("Qt Produced/Items loaded", min_value=0, value=0)
with col3:
    if st.button("Add Log"):
        if quantity <= 0:
            st.error("❌ Quantity must be greater than 0")
        else:
            cursor.execute("SELECT value FROM config WHERE name=?", (selected_item,))
            unit_charge = cursor.fetchone()[0]
            total_charge = quantity * unit_charge
            cursor.execute(
                "INSERT INTO daily_log(date, item_name, quantity, labour_charges) VALUES(CURRENT_DATE, ?, ?, ?)",
                (selected_item, quantity, total_charge)
            )
            conn.commit()
            st.success(f"✅ Log added! Total labour charges: ₹ {total_charge:,.2f}")

st.markdown("---")

# --- Summary cards ---
cursor.execute("""
    SELECT SUM(quantity), SUM(labour_charges)
    FROM daily_log
    WHERE date = CURRENT_DATE
    AND item_name = 'TILE'
""")
total_qty, total_charges = cursor.fetchone()
total_qty = total_qty or 0
total_charges = total_charges or 0.0

# cursor.execute("SELECT SUM(amount) FROM labour_payments")
# total_paid = cursor.fetchone()[0] or 0.0

col1, col2, col3 = st.columns(3)
col1.metric("Total Tiles Today", total_qty)
col2.metric("Total Labour Charges Today", f"₹ {total_charges:,.2f}")
# col3.metric("💰 Total Paid (All-time)", f"₹ {total_paid:,.2f}")

st.markdown("---")

# --- Show logs table ---
st.subheader("📋 Daily Logs Table")
df_logs = pd.read_sql("SELECT * FROM daily_log ORDER BY date DESC", conn)
st.dataframe(df_logs, use_container_width=True)



# --- Edit / Delete functionality inside Expander ---
with st.expander("✏️ Edit or Delete Entry", expanded=False):
    log_ids = df_logs['id'].tolist()
    if log_ids:
        selected_id = st.selectbox("Select entry ID to edit/delete", log_ids)

        if selected_id:
            selected_row = df_logs[df_logs['id'] == selected_id].iloc[0]
            edit_item = st.selectbox("Item", items, index=items.index(selected_row['item_name']))
            edit_qty = st.number_input("Quantity", min_value=0, value=int(selected_row['quantity']), key='edit_qty')

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Update Entry"):
                    if edit_qty <= 0:
                        st.error("❌ Quantity must be greater than 0")
                    else:
                        cursor.execute("SELECT value FROM config WHERE name=?", (edit_item,))
                        unit_charge = cursor.fetchone()[0]
                        total_charge = edit_qty * unit_charge
                        cursor.execute(
                            "UPDATE daily_log SET item_name=?, quantity=?, labour_charges=? WHERE id=?",
                            (edit_item, edit_qty, total_charge, selected_id)
                        )
                        conn.commit()
                        st.success("✅ Entry updated!")

            with col2:
                if st.button("Delete Entry"):
                    cursor.execute("DELETE FROM daily_log WHERE id=?", (selected_id,))
                    conn.commit()
                    st.warning("🗑️ Entry deleted!")


conn.close()
