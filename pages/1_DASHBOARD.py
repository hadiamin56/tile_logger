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
total_paid_all = total_paid + material_paid

# ------------------- Card Style -------------------
card_style = """
    <div style="
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin: 5px;
    ">
        <h4 style="margin-bottom: 8px;">{title}</h4>
        <h2 style="color:#2E86C1;">{value}</h2>
    </div>
"""

st.markdown("### 📊 Summary Overview")

# --- Tile Production ---
col1, col2 = st.columns(2)
with col1:
    st.markdown(card_style.format(title="Total Tiles Produced", value=f"{total_tiles}"), unsafe_allow_html=True)
with col2:
    st.markdown(card_style.format(title="Paid to Labour", value=f"₹ {total_paid:,.2f}"), unsafe_allow_html=True)

st.markdown("---")

# --- Labour Summary ---
st.markdown("#### 👷 Labour Summary")
col3, col4, col5 = st.columns(3)
with col3:
    st.markdown(card_style.format(title="Total Labour Charges", value=f"₹ {labour_charges:,.2f}"), unsafe_allow_html=True)
with col4:
    st.markdown(card_style.format(title="Paid to Labour", value=f"₹ {total_paid:,.2f}"), unsafe_allow_html=True)
with col5:
    st.markdown(card_style.format(title="Outstanding Balance", value=f"₹ {labour_balance:,.2f}"), unsafe_allow_html=True)

st.markdown("---")

# --- Material Summary ---
st.markdown("#### 🧱 Material Summary")
col6, col7, col8 = st.columns(3)
with col6:
    st.markdown(card_style.format(title="Material Expense", value=f"₹ {material_expense:,.2f}"), unsafe_allow_html=True)
with col7:
    st.markdown(card_style.format(title="Paid for Materials", value=f"₹ {material_paid:,.2f}"), unsafe_allow_html=True)
with col8:
    st.markdown(card_style.format(title="Outstanding Balance", value=f"₹ {material_balance:,.2f}"), unsafe_allow_html=True)

st.markdown("---")

# --- Overall Summary ---
st.markdown("#### 📦 Overall Summary")
col9, col10 = st.columns(2)
with col9:
    st.markdown(card_style.format(title="💰 Total Expense", value=f"₹ {total_expense:,.2f}"), unsafe_allow_html=True)
with col10:
    st.markdown(card_style.format(title="🏷️ Total Paid", value=f"₹ {total_paid_all:,.2f}"), unsafe_allow_html=True)

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
