import streamlit as st
import pandas as pd
from db import get_conn

st.set_page_config(page_title="Tiles Factory Dashboard", layout="wide")
st.title("🏭 Tiles Factory Dashboard")

# --- DB Connection ---
conn = get_conn()
cursor = conn.cursor()

# --- Fetch Config ---
df_config = pd.read_sql("SELECT * FROM config", conn)
config_dict = {(row['category'], row['option_name']): row['value'] for idx, row in df_config.iterrows()}

tile_rate = config_dict.get(("Tile", "1x1"), 5)
pot_rate = config_dict.get(("Pot", "Standard"), 10)
loading_rate = config_dict.get(("General", "LOADING"), 0.25)

# --- Summary Data ---
cursor.execute("SELECT SUM(labour_charges) FROM daily_log")
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

# ------------------- Card Template -------------------
def card_box(title, items):
    html = f"""
    <div style="background-color:#f8f9fa; padding:20px; border-radius:15px;
                box-shadow:0px 2px 8px rgba(0,0,0,0.1); margin:5px;">
        <h4 style="margin-bottom:15px; text-align:center;">{title}</h4>
    """
    for label, value in items:
        html += f"<p><b>{label}:</b> {value}</p>"
    html += "</div>"
    return html

# ------------------- Dashboard Layout -------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown(
        card_box("👷 Labour Summary", [
            ("Total Labour Charges", f"₹ {labour_charges:,.2f}"),
            ("Paid to Labour", f"₹ {total_paid:,.2f}"),
            ("Outstanding Balance", f"₹ {labour_balance:,.2f}")
        ]),
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        card_box("🧱 Material Summary", [
            ("Material Expense", f"₹ {material_expense:,.2f}"),
            ("Paid for Materials", f"₹ {material_paid:,.2f}"),
            ("Outstanding Balance", f"₹ {material_balance:,.2f}")
        ]),
        unsafe_allow_html=True
    )

col3, col4 = st.columns(2)

with col3:
    st.markdown(
        card_box("📦 Overall Summary", [
            ("Total Expense", f"₹ {total_expense:,.2f}"),
            ("Total Paid", f"₹ {total_paid_all:,.2f}")
        ]),
        unsafe_allow_html=True
    )

# ------------------- Tiles Production Breakdown -------------------
cursor.execute("""
    SELECT item_name, SUM(quantity) as total_qty
    FROM daily_log
    WHERE date = CURRENT_DATE
    AND (item_name LIKE 'Tile%' OR item_name LIKE 'Interlock%')
    GROUP BY item_name
""")
tile_rows = cursor.fetchall()

total_tiles_produced = 0
tile_1x1_qty = 0
interlock_qty = {}

for item_name, qty in tile_rows:
    total_tiles_produced += qty
    name_upper = item_name.upper()
    if "1X1" in name_upper:
        tile_1x1_qty += qty
    elif "INTERLOCK" in name_upper:
        size = name_upper.replace("INTERLOCK", "").strip()
        interlock_qty[size] = interlock_qty.get(size, 0) + qty

tile_items = [("Total Tiles Produced", total_tiles_produced),
              ("1x1", tile_1x1_qty)]
for size, qty in interlock_qty.items():
    tile_items.append((f"Interlock {size}", qty))

with col4:
    st.markdown(card_box("🏭 Tiles Production Breakdown", tile_items), unsafe_allow_html=True)

# ------------------- Data Tables -------------------
tab1, tab2, tab3 = st.tabs(["📋 Daily Log", "💵 Labour Payments", "🧾 Material Expenses"])

with tab1:
    st.subheader("📋 Daily Log")
    df_log = pd.read_sql("SELECT * FROM daily_log ORDER BY date DESC", conn)
    if "id" in df_log.columns:
        df_log = df_log.drop(columns=["id"])
    df_log = df_log.rename(columns=str.upper)
    st.dataframe(df_log, use_container_width=True)

with tab2:
    st.subheader("💵 Labour Payment History")
    df_payments = pd.read_sql("SELECT * FROM labour_payments ORDER BY date DESC", conn)
    if "id" in df_payments.columns:
        df_payments = df_payments.drop(columns=["id"])
    df_payments = df_payments.rename(columns=str.upper)
    st.dataframe(df_payments, use_container_width=True)

with tab3:
    st.subheader("🧾 Material Expense Records")
    df_materials = pd.read_sql("SELECT * FROM materials ORDER BY date DESC", conn)
    if "id" in df_materials.columns:
        df_materials = df_materials.drop(columns=["id"])
    df_materials = df_materials.rename(columns=str.upper)
    st.dataframe(df_materials, use_container_width=True)

# Close connection
conn.close()
