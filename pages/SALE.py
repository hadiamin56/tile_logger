import streamlit as st
import pandas as pd
from db import get_conn
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# --- Streamlit config ---
st.set_page_config(page_title="Sale", layout="wide")
st.title("🏪 Sale Management")

# --- DB connection ---
conn = get_conn()
cursor = conn.cursor()

# --- Fetch tile types from config ---
df_config = pd.read_sql("SELECT name, value FROM config", conn)
tile_types = df_config[~df_config["name"].isin(["TILE", "LOADING", "POT"])]
tile_options = tile_types["name"].tolist()

# --- Safe rerun helper (works for both old and new Streamlit versions) ---
def safe_rerun():
    if hasattr(st, "rerun"):  # Streamlit >=1.30
        st.rerun()
    elif hasattr(st, "experimental_rerun"):  # Streamlit <1.30
        st.experimental_rerun()

# --- Customer Billing Form ---
with st.expander("🧾 Customer Billing"):
    customer_name = st.text_input("Customer Name")
    customer_phone_number = st.text_input("Phone Number")
    tile_type = st.selectbox("Tile Type", tile_options)
    quantity = st.number_input("Quantity (tiles)", min_value=1, value=1)

    # Get price per tile from config
    price_per_tile = df_config[df_config["name"] == tile_type]["value"].astype(float).values[0]
    total_amount = price_per_tile * quantity
    st.markdown(f"💰 **Total Amount: ₹ {total_amount:.2f}**")

    payment_mode = st.selectbox("Payment Mode", ["Cash", "Online", "Wozum"])

    if st.button("Add Sale"):
        if customer_name.strip() == "":
            st.error("❌ Customer name cannot be empty")
        else:
            cursor.execute(
                """
                INSERT INTO sale (customer_name, customer_phone_number, tile_type, quantity, price_per_tile, amount, payment_mode, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    customer_name,
                    customer_phone_number,
                    tile_type,
                    quantity,
                    price_per_tile,
                    total_amount,
                    payment_mode,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            conn.commit()
            st.success(f"✅ Sale added for {customer_name} | Amount: ₹ {total_amount:.2f}")
            safe_rerun()  # <--- safe refresh

# --- Helper: Generate professional invoice PDF ---
def generate_invoice_pdf(row):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Thin border
    c.setLineWidth(0.5)
    c.rect(20, 20, width-40, height-40)

    # Company info
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, height - 50, "Tile Factory Seeloo")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, "Seeloo, Sopore 193201")
    c.drawString(50, height - 85, "Contact: 7006363824 | Email: hadiamin56@gmail.com")
    c.drawString(50, height - 100, "GST: jksdafhksajdhfasiu")

    # Invoice title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 140, "SALES INVOICE")

    # Customer and sale details
    c.setFont("Helvetica", 12)
    y = height - 180
    line_height = 18
    c.drawString(50, y, f"Customer Name: {row['customer_name']}")
    y -= line_height
    c.drawString(50, y, f"Phone: {row['customer_phone_number']}")
    y -= line_height
    c.drawString(50, y, f"Tile Type: {row['tile_type']}")
    y -= line_height
    c.drawString(50, y, f"Quantity: {row['quantity']}")
    y -= line_height
    c.drawString(50, y, f"Price per Tile: ₹ {row['price_per_tile']:.2f}")
    y -= line_height
    c.drawString(50, y, f"Total Amount: ₹ {row['amount']:.2f}")
    y -= line_height
    c.drawString(50, y, f"Payment Mode: {row['payment_mode']}")
    y -= line_height
    c.drawString(50, y, f"Date: {row['date']}")

    # Footer
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, 50, "Thank you for your business!")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- Sales List Table with Download Button ---
st.subheader("📋 Sales List")
df_sales = pd.read_sql(
    "SELECT id, customer_name, customer_phone_number, tile_type, quantity, price_per_tile, amount, payment_mode, date FROM sale",
    conn,
)

if not df_sales.empty:
    # Fixed column ratio (same for header + rows)
    col_ratio = [1, 2, 2, 2, 1, 1, 1.5, 2, 2, 1]
    headers = ["ID","Customer","Phone","Tile Type","Qty","Price","Amount","Payment","Date","Invoice"]

    # Header row
    cols = st.columns(col_ratio)
    for col, header in zip(cols, headers):
        col.markdown(f"**{header}**")

    # Data rows
    for _, row in df_sales.iterrows():
        cols = st.columns(col_ratio)
        cols[0].write(row['id'])
        cols[1].write(row['customer_name'])
        cols[2].write(row['customer_phone_number'])
        cols[3].write(row['tile_type'])
        cols[4].write(row['quantity'])
        cols[5].write(f"₹{row['price_per_tile']:.2f}")
        cols[6].write(f"₹{row['amount']:.2f}")
        cols[7].write(row['payment_mode'])

        # Only date part
        if isinstance(row['date'], str):
            date_only = row['date'].split(' ')[0]
        else:
            date_only = row['date'].date()
        cols[8].write(str(date_only))

        # Download button
        pdf_buffer = generate_invoice_pdf(row)
        cols[9].download_button(
            label="Download",
            data=pdf_buffer,
            file_name=f"invoice_{row['id']}.pdf",
            mime="application/pdf",
            key=f"download_{row['id']}",
            use_container_width=True,
        )
else:
    st.info("No sales added yet.")

conn.close()
