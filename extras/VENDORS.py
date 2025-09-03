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
