import streamlit as st
import pandas as pd
from db import get_conn
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Register font for Unicode (₹ symbol)
font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))
    FONT_NAME = "DejaVuSans"
else:
    FONT_NAME = "Helvetica"

# ------------------ PDF GENERATION ------------------
def generate_invoice_pdf(data, customer_name, customer_phone, payment_mode, sale_date, sale_id):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # ---- Watermark ----
    c.saveState()
    c.setFont(FONT_NAME, 60)
    c.setFillColorRGB(0.9, 0.9, 0.9)  # Light gray watermark
    c.translate(width / 2, height / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, "TILE FACTORY SEELOO")
    c.restoreState()

    c.setFont(FONT_NAME, 10)

    # ---- Page Border ----
    c.setStrokeColorRGB(0.6, 0.6, 0.6)
    c.setLineWidth(0.7)
    c.rect(30, 30, width - 60, height - 60)

    # ---- Header ----
    c.setFont(FONT_NAME, 14)
    c.drawString(50, height - 50, "Tiles Factory Seeloo")
    c.setFont(FONT_NAME, 10)
    c.drawString(50, height - 65, "Near Hi Five Agro Skills, Seeloo, Sopore")
    c.drawString(50, height - 80, "Phone: +91-7006363824")

    c.setFont(FONT_NAME, 16)
    c.drawRightString(width - 50, height - 50, "INVOICE")

    c.setFont(FONT_NAME, 10)
    c.drawRightString(width - 50, height - 80, f"Invoice #: {sale_id}")
    c.drawRightString(width - 50, height - 95, f"Date: {sale_date}")

    # ---- Bill To ----
    y = height - 140
    c.setFont(FONT_NAME, 11)
    c.drawString(50, y, "Bill To:")
    c.setFont(FONT_NAME, 10)
    c.drawString(50, y - 15, f"{customer_name}")
    c.drawString(50, y - 30, f"Phone: {customer_phone}")
    c.drawString(50, y - 45, f"Payment Mode: {payment_mode}")

    # ---- Items Box ----
    box_top = y - 80
    box_height = 300
    box_width = width - 100
    start_x = 50
    start_y = box_top - box_height

    # Outer big box
    c.setStrokeColorRGB(0.6, 0.6, 0.6)
    c.rect(start_x, start_y, box_width, box_height)

    # Column vertical lines
    col_widths = [box_width * 0.4, box_width * 0.2, box_width * 0.2, box_width * 0.2]
    x_positions = [start_x + sum(col_widths[:i]) for i in range(len(col_widths) + 1)]
    for x in x_positions:
        c.line(x, start_y, x, box_top)

    # Table Headers
    headers = ["ITEM NAME", "UNIT PRICE(Rs)", "Quantity(No)", "TOTAL(Rs)"]
    c.setFont(FONT_NAME, 10)
    for i, h in enumerate(headers):
        c.drawString(x_positions[i] + 5, box_top - 15, h)

    # Line below header
    header_line_y = box_top - 25
    c.line(start_x, header_line_y, start_x + box_width, header_line_y)

    # Table Data
    c.setFont(FONT_NAME, 10)
    row_height = 20
    y_pos = header_line_y - 20
    for _, row in data.iterrows():
        values = [
            row["tile_type"],
            f"{row['price_per_tile']:.2f}",
            str(row["quantity"]),
            f"{row['amount']:.2f}",
        ]
        for i, val in enumerate(values):
            c.drawString(x_positions[i] + 5, y_pos, val)
        y_pos -= row_height

    # ---- Total Amount Row ----
    total_y = start_y + 20
    c.line(start_x, total_y + 20, start_x + box_width, total_y + 20)
    c.setFont(FONT_NAME, 11)
    c.drawString(start_x + 5, total_y + 5, "Total Amount:")
    c.drawRightString(start_x + box_width - 5, total_y + 5, f"{data['amount'].sum():.2f}")

    # ---- Footer ----
    c.setFont(FONT_NAME, 10)
    right_margin = width - 50
    c.drawRightString(right_margin, 60, "Additional Information/Comments:")
    c.drawRightString(right_margin, 40, "Authorized Signatory")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ------------------ STREAMLIT APP ------------------
st.set_page_config(page_title="🧾 Generate Invoice", layout="centered")
st.title("🧾 Invoice Generator")

conn = get_conn()
df_sales = pd.read_sql("SELECT * FROM sale ORDER BY date DESC", conn)

# Convert date column to datetime
df_sales["date"] = pd.to_datetime(df_sales["date"], errors="coerce")

if df_sales.empty:
    st.warning("⚠️ No sales available to generate invoice.")
    st.stop()

# ---- Optional Date Filter ----
date_filter = st.checkbox("Filter by Date")
if date_filter:
    selected_date = st.date_input("Select Date")
    df_sales = df_sales[df_sales["date"].dt.date == selected_date]

if df_sales.empty:
    st.warning("⚠️ No sales for selected date.")
    st.stop()

# ---- Dropdown with only Customer Names ----
sale_ids = df_sales["sale_id"].unique()
sale_labels = {sid: df_sales[df_sales["sale_id"] == sid]["customer_name"].iloc[0] for sid in sale_ids}

selected_customer = st.selectbox("Select Customer", list(sale_labels.values()))
selected_sale = [sid for sid, name in sale_labels.items() if name == selected_customer][0]

# ---- Filter Sale Data ----
sale_data = df_sales[df_sales["sale_id"] == selected_sale]
customer_name = sale_data["customer_name"].iloc[0]
customer_phone = sale_data["customer_phone_number"].iloc[0]
payment_mode = sale_data["payment_mode"].iloc[0]
sale_date = sale_data["date"].iloc[0]

st.subheader("🧱 Sale Items")
st.dataframe(sale_data[["tile_type", "quantity", "price_per_tile", "amount"]], use_container_width=True)

# ---- Download PDF ----
pdf_file = generate_invoice_pdf(sale_data, customer_name, customer_phone, payment_mode, sale_date, selected_sale)

st.download_button(
    label="📥 Download Invoice as PDF",
    data=pdf_file,
    file_name=f"Invoice_{selected_sale}.pdf",
    mime="application/pdf"
)

