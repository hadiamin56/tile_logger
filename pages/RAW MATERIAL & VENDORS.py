import streamlit as st

# Create tabs for the two apps
tab1, tab2 = st.tabs(["Raw Material", "Vendors"])

# ---------------- TAB 1: Sales Dashboard ----------------
with tab1:
    # --- Code from sale.py goes here ---
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
                        if pay_amount <= 0:
                            st.error("❌ Payment amount must be greater than 0!")
                        elif pay_amount > vendor_balance:
                            st.error("⚠️ Payment exceeds remaining balance!")
                        else:
                            add_payment(vendor_id, str(pay_date), pay_amount)
                            st.success("✅ Payment added successfully!")
                            st.rerun()

# ---------------- TAB 2: Invoice Generator ----------------
with tab2:
    # --- Code from invoice.py goes here ---
    import streamlit as st
    import pandas as pd
    from db import get_conn

    st.set_page_config(page_title="Vendors", layout="wide")
    st.title("🏪 Vendor Management")

    # --- DB Connection ---
    conn = get_conn()
    cursor = conn.cursor()

    # Ensure vendor_materials table exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendor_materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vendor_id INTEGER,
        material_name TEXT,
        FOREIGN KEY(vendor_id) REFERENCES vendors(id)
    )
    ''')
    conn.commit()

    # --- Add New Vendor ---
    with st.expander("Add New Vendor"):
        name = st.text_input("Vendor Name")
        phone = st.text_input("Phone Number")
        details = st.text_area("Additional Details")

        # Raw materials list
        material_options = ["Cement", "Chemical", "Color", "Bajri", "Sand", "Mould"]
        selected_materials = st.multiselect("Select Materials Provided", material_options)

        if st.button("Add Vendor"):
            if name.strip() == "":
                st.error("Vendor name cannot be empty")
            else:
                cursor.execute(
                    "INSERT INTO vendors(name, phone, details) VALUES (?, ?, ?)",
                    (name, phone, details)
                )
                vendor_id = cursor.lastrowid  # new vendor id

                # Insert selected materials
                for mat in selected_materials:
                    cursor.execute(
                        "INSERT INTO vendor_materials(vendor_id, material_name) VALUES (?, ?)",
                        (vendor_id, mat)
                    )

                conn.commit()
                st.success(f"Vendor '{name}' added with materials: {', '.join(selected_materials)}")

    # --- Show Vendors ---
    st.subheader("📋 Vendor List")
    vendors_df = pd.read_sql("SELECT id, name, phone, details FROM vendors", conn)

    if not vendors_df.empty:
        # Fetch vendor-materials mapping
        materials_df = pd.read_sql("SELECT vendor_id, material_name FROM vendor_materials", conn)
        material_map = materials_df.groupby("vendor_id")["material_name"].apply(list).to_dict()

        vendors_df["Materials"] = vendors_df["id"].map(material_map).fillna("").apply(
            lambda x: ", ".join(x) if isinstance(x, list) else ""
        )

        st.dataframe(
            vendors_df.drop(columns=["id"]).rename(columns=str.upper),
            use_container_width=True
        )
    else:
        st.info("No vendors added yet.")

    # --- Delete Vendor ---
    with st.expander("Delete Vendor"):
        vendors = pd.read_sql("SELECT id, name FROM vendors", conn)
        if not vendors.empty:
            vendor_choice = st.selectbox("Select Vendor to Delete", vendors["name"])
            if st.button("Delete Vendor"):
                vendor_id = vendors[vendors["name"] == vendor_choice]["id"].values[0]
                cursor.execute("DELETE FROM vendor_materials WHERE vendor_id=?", (vendor_id,))
                cursor.execute("DELETE FROM vendors WHERE id=?", (vendor_id,))
                conn.commit()
                st.success(f"Vendor '{vendor_choice}' deleted!")
        else:
            st.warning("No vendors available to delete.")

    # --- Close Connection ---
    conn.close()

