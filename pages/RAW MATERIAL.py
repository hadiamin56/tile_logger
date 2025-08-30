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

def get_vendor_materials(vendor_id):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT material_name FROM vendor_materials WHERE vendor_id=?", (vendor_id,))
    mats = [row[0] for row in cursor.fetchall()]
    conn.close()
    return mats

def add_material(date, material_type, unit, quantity, price_per_unit, vendor_id):
    total_price = quantity * price_per_unit
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO materials (date, material_type, quantity, unit, price_per_unit, total_price, vendor_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date, material_type, quantity, unit, price_per_unit, total_price, vendor_id))
    conn.commit()
    conn.close()

def get_materials():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT m.date, m.material_type, m.quantity, m.unit, m.price_per_unit, m.total_price, v.id, v.name
        FROM materials m
        JOIN vendors v ON m.vendor_id = v.id
        ORDER BY v.name, m.date DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

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

# --- Add Material Procurement ---
with st.expander("➕ Add New Material Procurement"):
    vendors = get_all_vendors()
    if not vendors:
        st.warning("⚠️ Please add vendors in the vendors table first!")
    else:
        vendor_map = {v[1]: v[0] for v in vendors}
        vendor_name = st.selectbox("Select Vendor", list(vendor_map.keys()))
        vendor_id = vendor_map[vendor_name]

        # Get vendor's allowed materials
        vendor_mats = get_vendor_materials(vendor_id)
        if not vendor_mats:
            st.info("This vendor has no materials assigned yet. Please update vendor details first.")
        else:
            st.write("### Select Materials to Procure")

            with st.form("procurement_form"):
                date = st.date_input("Date")
                entries = []

                for mat in vendor_mats:
                    st.markdown(f"**{mat}**")
                    cols = st.columns(3)
                    qty = cols[0].number_input(f"Quantity ({mat})", min_value=0, step=1, key=f"qty_{mat}")
                    price = cols[1].number_input(f"Price per unit ({mat})", min_value=0.0, step=0.1, key=f"ppu_{mat}")
                    unit = cols[2].text_input(f"Unit ({mat})", value="bags", key=f"unit_{mat}")

                    if qty > 0 and price > 0:
                        total = qty * price
                        st.write(f"💰 Total for {mat}: ₹ {total:,.2f}")
                        entries.append((mat, unit, qty, price, total))

                submitted = st.form_submit_button("Add Procurement")
                if submitted and entries:
                    for (mat, unit, qty, price, total) in entries:
                        add_material(str(date), mat, unit, qty, price, vendor_id)
                    st.success("✅ Procurement records added successfully!")
                    st.rerun()

# --- Display Materials & Payments ---
materials = get_materials()
if not materials:
    st.info("No materials added yet.")
else:
    df = pd.DataFrame(materials, columns=["Date","Material","Quantity","Unit","Price/Unit","Total Price","Vendor_ID","Vendor"])
    
    vendor_totals = df.groupby("Vendor").agg({"Total Price":"sum"}).reset_index()
    
    for _, row in vendor_totals.iterrows():
        vendor_name = row["Vendor"]
        total_price = row["Total Price"]
        cols = st.columns([2, 1, 1])
        cols[0].write(vendor_name)
        cols[1].write(f"₹ {total_price:,.2f}")
        
        if vendor_name not in st.session_state.view_flags:
            st.session_state.view_flags[vendor_name] = False
        if cols[2].button("View Details", key=f"view_{vendor_name}"):
            st.session_state.view_flags[vendor_name] = not st.session_state.view_flags[vendor_name]

        if st.session_state.view_flags[vendor_name]:
            vendor_items = df[df["Vendor"] == vendor_name][["Date","Material","Quantity","Unit","Price/Unit","Total Price"]]
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
                        st.rerun()
