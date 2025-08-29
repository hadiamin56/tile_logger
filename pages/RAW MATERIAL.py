import streamlit as st
import pandas as pd
from db import get_conn

# --- Helper functions ---
def get_all_vendors():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM vendors ORDER BY name")
    vendors = cursor.fetchall()
    conn.close()
    return vendors

def get_materials():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.id, m.date, m.material_type, m.unit, m.price, v.id, v.name
        FROM materials m
        JOIN vendors v ON m.vendor_id = v.id
        ORDER BY v.name, m.date DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_material(date, material_type, unit, vendor_id, price):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO materials (date, material_type, unit, price, vendor_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (date, material_type, unit, price, vendor_id))
    conn.commit()
    conn.close()

def add_payment(vendor_id, date, amount):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO material_payments (vendor_id, date, amount)
        VALUES (?, ?, ?)
    ''', (vendor_id, date, amount))
    conn.commit()
    conn.close()

def get_vendor_paid_total(vendor_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT IFNULL(SUM(amount),0) FROM material_payments WHERE vendor_id=?', (vendor_id,))
    paid = cursor.fetchone()[0]
    conn.close()
    return paid

def get_vendor_payments(vendor_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT date, amount FROM material_payments WHERE vendor_id=? ORDER BY date DESC', (vendor_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

# --- Initialize session state flags ---
if "view_flags" not in st.session_state:
    st.session_state.view_flags = {}

# --- UI ---
st.subheader("📋 Materials Procurement & Vendor Payments")

# --- Add Material Form ---
with st.expander("Add New Material Procurement"):
    with st.form("material_form"):
        date = st.date_input("Date")
        material_type = st.text_input("Material Type")
        unit = st.text_input("Unit (e.g. kg, bags, pieces)")

        vendors = get_all_vendors()
        if vendors:
            vendor_map = {v[1]: v[0] for v in vendors}
            vendor_name = st.selectbox("Vendor", list(vendor_map.keys()))
        else:
            st.warning("⚠️ Please add vendors in the vendors table first!")
            vendor_map, vendor_name = {}, None

        price = st.number_input("Total Price (₹)", min_value=0.0, step=0.1)
        submitted = st.form_submit_button("Add Material")
        if submitted and vendor_name:
            add_material(str(date), material_type, unit, vendor_map[vendor_name], price)
            st.success("✅ Material added successfully!")
            st.rerun()   # 👈 instantly refresh

# --- Display Aggregated Materials ---
materials = get_materials()
if not materials:
    st.info("No materials added yet.")
else:
    df = pd.DataFrame(materials, columns=["ID","Date","Material","Unit","Price","Vendor_ID","Vendor"])
    
    vendor_totals = df.groupby("Vendor").agg({"Price":"sum"}).reset_index()
    vendor_totals.rename(columns={"Price":"Total Price (₹)"}, inplace=True)
    
    for _, row in vendor_totals.iterrows():
        vendor_name = row["Vendor"]
        total_price = row["Total Price (₹)"]
        cols = st.columns([2, 1, 1])
        cols[0].write(vendor_name)
        cols[1].write(f"₹ {total_price:,.2f}")
        
        if vendor_name not in st.session_state.view_flags:
            st.session_state.view_flags[vendor_name] = False
        if cols[2].button("View Details", key=f"view_{vendor_name}"):
            st.session_state.view_flags[vendor_name] = not st.session_state.view_flags[vendor_name]

        if st.session_state.view_flags[vendor_name]:
            vendor_items = df[df["Vendor"] == vendor_name][["Date","Material","Unit","Price"]]
            st.text(f"📋 Details for {vendor_name}")
            st.dataframe(vendor_items, use_container_width=True)
            
            vendor_id = df[df["Vendor"] == vendor_name]["Vendor_ID"].iloc[0]
            vendor_paid = get_vendor_paid_total(vendor_id)
            vendor_balance = total_price - vendor_paid
            st.write(f"💵 Paid: ₹ {vendor_paid:,.2f} | 🏷️ Balance: ₹ {vendor_balance:,.2f}")
            
            payments = get_vendor_payments(vendor_id)
            if payments:
                st.write("📜 Payment History:")
                st.table([{"Date": p[0], "Amount": f"₹ {p[1]:,.2f}"} for p in payments])
            else:
                st.info("No payments recorded yet.")
            
            with st.form(f"payment_form_{vendor_id}"):
                pay_date = st.date_input("Payment Date", key=f"pdate_{vendor_id}")
                pay_amount = st.number_input("Payment Amount", min_value=0.0, step=0.1, key=f"pamt_{vendor_id}")
                pay_submit = st.form_submit_button("Add Payment")
                if pay_submit:
                    if pay_amount > vendor_balance:
                        st.error("⚠️ Payment exceeds remaining balance!")
                    else:
                        add_payment(vendor_id, str(pay_date), pay_amount)
                        st.success("✅ Payment added successfully!")
                        st.rerun()   # 👈 instantly refresh
