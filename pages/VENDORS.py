import streamlit as st
import pandas as pd
from db import get_conn

st.set_page_config(page_title="Vendors", layout="wide")
st.title("🏪 Vendor Management")

conn = get_conn()
cursor = conn.cursor()

# --- Create tables if not exist ---
# cursor.execute("""
# CREATE TABLE IF NOT EXISTS vendors (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     name TEXT NOT NULL,
#     phone TEXT,
#     details TEXT
# )
# """)
# conn.commit()

# --- Add New Vendor ---
with st.expander("Add New Vendor"):
    name = st.text_input("Vendor Name")
    phone = st.text_input("Phone Number")
    details = st.text_area("Additional Details")

    if st.button("Add Vendor"):
        if name.strip() == "":
            st.error("Vendor name cannot be empty")
        else:
            cursor.execute(
                "INSERT INTO vendors(name, phone, details) VALUES (?, ?, ?)",
                (name, phone, details)
            )
            conn.commit()
            st.success(f"Vendor '{name}' added!")

# --- Show Vendors ---
st.subheader("📋 Vendor List")
df_vendors = pd.read_sql("SELECT id, name, phone, details FROM vendors", conn)

if not df_vendors.empty:
    st.dataframe(df_vendors.drop(columns=["id"]), use_container_width=True)
else:
    st.info("No vendors added yet.")

# --- Delete Vendor ---
with st.expander("Delete Vendor"):
    vendors = pd.read_sql("SELECT id, name FROM vendors", conn)
    if not vendors.empty:
        vendor_choice = st.selectbox("Select Vendor to Delete", vendors["name"])
        if st.button("Delete Vendor"):
            vendor_id = vendors[vendors["name"] == vendor_choice]["id"].values[0]
            cursor.execute("DELETE FROM vendors WHERE id=?", (vendor_id,))
            conn.commit()
            st.success(f"Vendor '{vendor_choice}' deleted!")
    else:
        st.warning("No vendors available to delete.")

conn.close()
