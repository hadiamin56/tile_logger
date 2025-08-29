import streamlit as st
import pandas as pd
from db import get_conn

st.set_page_config(page_title="Tiles Factory Dashboard", layout="wide")
st.title("🏭 Tiles Factory Dashboard")

# --- DB Connection ---
conn = get_conn()
cursor = conn.cursor()

# --- Fetch Config ---
cursor.execute("SELECT name, value FROM config")
config = dict(cursor.fetchall())

tile_rate = config.get("tile", 5)
pot_rate = config.get("pot", 10)
loading_rate = config.get("loading", 0.25)

# --- Summary Data ---
cursor.execute("SELECT SUM(labour_charges) FROM daily_log")
labour_charges = cursor.fetchone()[0] or 0.0

cursor.execute("SELECT SUM(quantity) FROM daily_log where item_name='TILE'")
total_tiles = cursor.fetchone()[0] or 0.0


cursor.execute("SELECT SUM(amount) FROM labour_payments")
total_paid = cursor.fetchone()[0] or 0.0

cursor.execute("SELECT SUM(price) FROM materials")
material_expense = cursor.fetchone()[0] or 0.0

cursor.execute("SELECT SUM(amount) FROM material_payments")
material_paid = cursor.fetchone()[0] or 0.0

labour_balance = labour_charges - total_paid
material_balance = material_expense - material_paid
total_expense = material_expense + labour_charges
total_paid_all = total_paid+material_paid
# ------------------- Dashboard Layout -------------------
st.markdown("### 📊 Summary Overview")

# Labour Section
with st.container():
    st.markdown("#### 👷Tile Production")
    col1, col2 = st.columns(2)
    col1.metric("Total Tiles Produced", f"{total_tiles}")
    # col2.metric("Paid to Labour", f"₹ {total_paid:,.2f}")
    col2.metric("Paid to Labour", "test")


st.markdown("---")

# Labour Section
with st.container():
    st.markdown("#### 👷 Labour Summary")
    col3, col4, col5 = st.columns(3)
    col3.metric("Total Labour Charges", f"₹ {labour_charges:,.2f}")
    col4.metric("Paid to Labour", f"₹ {total_paid:,.2f}")
    col5.metric("Outstanding Balance", f"₹ {labour_balance:,.2f}")

st.markdown("---")


# Material Section
with st.container():
    st.markdown("#### 🧱 Material Summary")
    col6, col7, col8 = st.columns(3)
    col6.metric("Material Expense", f"₹ {material_expense:,.2f}")
    col7.metric("Paid for Materials", f"₹ {material_paid:,.2f}")
    col8.metric("Outstanding Balance", f"₹ {material_balance:,.2f}")

st.markdown("---")

# Total Section
with st.container():
    st.markdown("#### 📦 Overall Summary")
    col9, col10= st.columns(2)
    col9.metric("💰 Total Expense", f"₹ {total_expense:,.2f}")
    col10.metric("🏷️ Total Paid", f"₹ {total_paid_all:,.2f} ")

st.markdown("---")

# ------------------- Data Tables -------------------
tab1, tab2, tab3 = st.tabs(["📋 Daily Log", "💵 Labour Payments", "🧾 Material Expenses"])

with tab1:
    st.subheader("📋 Daily Log")
    df_log = pd.read_sql("SELECT * FROM daily_log ORDER BY date DESC", conn)
    st.dataframe(df_log, use_container_width=True)

with tab2:
    st.subheader("💵 Labour Payment History")
    df_payments = pd.read_sql("SELECT * FROM labour_payments ORDER BY date DESC", conn)
    st.dataframe(df_payments, use_container_width=True)

with tab3:
    st.subheader("🧾 Material Expense Records")
    df_materials = pd.read_sql("SELECT * FROM materials ORDER BY date DESC", conn)
    st.dataframe(df_materials, use_container_width=True)

# Close connection
conn.close()
