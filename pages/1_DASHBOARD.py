import streamlit as st
import pandas as pd
from db import get_conn
# import plotly.express as px

st.set_page_config(page_title="Tiles Factory Dashboard", layout="wide")
st.title("🏭 Tiles Factory Dashboard")

# --- DB Connection ---
conn = get_conn()
cursor = conn.cursor()

# --- Summary Data ---
cursor.execute("SELECT SUM(labour_charge) FROM daily_log")
labour_charges = cursor.fetchone()[0] or 0.0

cursor.execute("SELECT SUM(amount) FROM labour_payments")
total_paid = cursor.fetchone()[0] or 0.0

cursor.execute("SELECT SUM(total_price) FROM materials")
material_expense = cursor.fetchone()[0] or 0.0

cursor.execute("SELECT SUM(amount) FROM material_payments")
material_paid = cursor.fetchone()[0] or 0.0

labour_balance = labour_charges - total_paid
material_balance = material_expense - material_paid
total_expense = labour_charges + material_expense
total_paid_all = total_paid + material_paid

# --- Tiles Data ---
cursor.execute("""
    SELECT tile_type, interlock_subtype, interlock_size, color, SUM(quantity) as total_qty
    FROM daily_log
    WHERE category = 'Tile'
    GROUP BY tile_type, interlock_subtype, interlock_size, color
""")
tile_rows = cursor.fetchall()
df_tiles = pd.DataFrame(tile_rows, columns=["Tile Type", "Subtype", "Size", "Color", "Quantity"])
total_tiles_produced = df_tiles["Quantity"].sum() if not df_tiles.empty else 0

cursor.execute("SELECT SUM(quantity), SUM(amount) FROM sale")
tiles_sold_data = cursor.fetchone()
total_tiles_sold = tiles_sold_data[0] or 0
total_sales_amount = tiles_sold_data[1] or 0.0

# ------------------- KPI CARDS SINGLE LINE WITH ICONS -------------------
def kpi_card(title, value, color, icon):
    return f"""
    <div style="
        background-color:{color};
        padding:12px;
        border-radius:12px; 
        text-align:center;
        color:white;
        font-size:13px;
        font-weight:bold;
        width:140px;  /* Reduced width to fit all cards in one line */
        margin:5px;
        box-shadow:0 2px 6px rgba(0,0,0,0.1);
        flex-shrink:0;
        display:flex;
        flex-direction:column;
        justify-content:center;
        align-items:center;
    ">
        <div style="font-size:20px; margin-bottom:6px;">{icon}</div>
        <h4 style="margin:0; font-size:12px; text-align:center; white-space:normal; word-wrap:break-word;">
            {title}
        </h4>
        <p style="margin:0; font-size:14px; text-align:center; white-space:normal; word-wrap:break-word;">
            {value}
        </p>
    </div>
    """

kpi1 = kpi_card("Total Expense", f"₹ {total_expense:,.2f}", "#6c757d", "💰")
kpi2 = kpi_card("Total Paid", f"₹ {total_paid_all:,.2f}", "#198754", "✅")
kpi3 = kpi_card("Tiles Produced", f"{total_tiles_produced:,}", "#0d6efd", "🧱")
kpi4 = kpi_card("Tiles Sold", f"{total_tiles_sold:,}", "#ffc107", "📦")
kpi5 = kpi_card("Sales Amount", f"₹ {total_sales_amount:,.2f}", "#dc3545", "💵")

st.markdown(f"""
    <div style="
        display:flex; 
        justify-content:center; 
        flex-wrap:nowrap;  /* Keep all cards in single line */
        gap:8px;
    ">
        {kpi1} {kpi2} {kpi3} {kpi4} {kpi5}
    </div>
""", unsafe_allow_html=True)

# ------------------- CHART -------------------
# if not df_tiles.empty:
#     st.subheader("📊 Tiles Production vs Sales")
#     df_chart = pd.DataFrame({
#         "Metric": ["Produced", "Sold"],
#         "Quantity": [total_tiles_produced, total_tiles_sold]
#     })
#     fig = px.bar(df_chart, x="Metric", y="Quantity", color="Metric", text="Quantity", title="Tiles Production vs Sales")
#     st.plotly_chart(fig, use_container_width=True)

# ------------------- TILE DETAILS -------------------
if not df_tiles.empty:
    st.subheader("📋 Tile Production Details")
    df_1x1 = df_tiles[df_tiles["Tile Type"] == "1x1"]
    df_interlock = df_tiles[df_tiles["Tile Type"] != "1x1"]

    if not df_1x1.empty:
        with st.expander(f"1x1 Tiles (Total: {df_1x1['Quantity'].sum()})", expanded=True):
            st.dataframe(df_1x1[["Color", "Quantity"]].sort_values("Quantity", ascending=False), use_container_width=True)

    if not df_interlock.empty:
        for subtype, df_sub in df_interlock.groupby("Subtype"):
            with st.expander(f"{subtype} (Total: {df_sub['Quantity'].sum()})", expanded=False):
                st.dataframe(df_sub[["Size", "Color", "Quantity"]].sort_values(["Size", "Color"]), use_container_width=True)

# ------------------- DATA TABLES -------------------
tab1, tab2, tab3 = st.tabs(["📋 Daily Log", "💵 Labour Payments", "🧾 Material Expenses"])

with tab1:
    st.subheader("📋 Daily Log")
    df_log = pd.read_sql("SELECT * FROM daily_log ORDER BY log_date DESC", conn)
    if "id" in df_log.columns: df_log = df_log.drop(columns=["id"])
    st.dataframe(df_log.rename(columns=str.upper), use_container_width=True)

with tab2:
    st.subheader("💵 Labour Payment History")
    df_payments = pd.read_sql("SELECT * FROM labour_payments ORDER BY date DESC", conn)
    if "id" in df_payments.columns: df_payments = df_payments.drop(columns=["id"])
    st.dataframe(df_payments.rename(columns=str.upper), use_container_width=True)

with tab3:
    st.subheader("🧾 Material Expense Records")
    df_materials = pd.read_sql("SELECT * FROM materials ORDER BY date DESC", conn)
    if "id" in df_materials.columns: df_materials = df_materials.drop(columns=["id"])
    st.dataframe(df_materials.rename(columns=str.upper), use_container_width=True)

conn.close()
