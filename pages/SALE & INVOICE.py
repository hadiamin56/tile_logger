import streamlit as st

# Create tabs for the two apps
tab1, tab2 = st.tabs(["🧱 Sales Dashboard", "🧾 Download Invoice "])

# ---------------- TAB 1: Sales Dashboard ----------------
with tab1:
    # --- Code from sale.py goes here ---
    import streamlit as st
    import pandas as pd
    from db import get_conn
    from datetime import datetime
    import uuid

    st.set_page_config(page_title="Tiles Sales Dashboard", layout="wide")
    st.markdown("<h1 style='text-align: center;'>🏪 Tiles Sales Dashboard</h1>", unsafe_allow_html=True)

    conn = get_conn()
    cur = conn.cursor()

    # ------------------------ HELPER FUNCTIONS ------------------------
    def parse_tile(tile_name):
        parts = tile_name.split()
        if parts[0] == "1x1":
            return pd.Series({
                "tile_type_parsed": "1x1",
                "interlock_subtype": "-",
                "interlock_size": "-",
                "color": parts[-1]
            })
        elif parts[0] == "Interlock":
            color = parts[-1]
            size = parts[-2]
            subtype = " ".join(parts[1:-2])
            return pd.Series({
                "tile_type_parsed": "Interlock",
                "interlock_subtype": subtype,
                "interlock_size": size,
                "color": color
            })
        else:
            return pd.Series({
                "tile_type_parsed": tile_name,
                "interlock_subtype": "-",
                "interlock_size": "-",
                "color": "-"
            })

    # ------------------------ LOAD DATA ------------------------
    df_daily = pd.read_sql("SELECT * FROM daily_log WHERE category='Tile'", conn)

    # Initial stock (from daily_log)
    df_stock = df_daily.groupby(
        ["tile_type", "interlock_subtype", "interlock_size", "color"], as_index=False
    )["quantity"].sum()
    df_stock.rename(columns={"quantity": "available_qty"}, inplace=True)

    # Sales data
    df_sales = pd.read_sql("SELECT * FROM sale ORDER BY date DESC", conn)

    # Current stock (daily_log - sold)
    if not df_sales.empty:
        df_sales[['tile_type_parsed', 'interlock_subtype', 'interlock_size', 'color']] = df_sales['tile_type'].apply(parse_tile)

        df_sold = df_sales.groupby(
            ["tile_type_parsed", "interlock_subtype", "interlock_size", "color"], as_index=False
        )["quantity"].sum()

        df_current_stock = pd.merge(
            df_stock,
            df_sold,
            left_on=["tile_type", "interlock_subtype", "interlock_size", "color"],
            right_on=["tile_type_parsed", "interlock_subtype", "interlock_size", "color"],
            how="left"
        ).fillna(0)

        df_current_stock["available_qty"] = df_current_stock["available_qty"] - df_current_stock["quantity"]
    else:
        df_current_stock = df_stock.copy()
        df_current_stock["quantity"] = 0

    df_current_stock = df_current_stock[["tile_type", "interlock_subtype", "interlock_size", "color", "available_qty", "quantity"]]

    # ------------------------ ADD SALE ------------------------
    with st.expander("➕ Add Sale", expanded=True):
        st.markdown("### 🧑 Customer Details")
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Customer Name")
        with col2:
            customer_phone = st.text_input("Phone Number")

        if "cart" not in st.session_state:
            st.session_state.cart = []

        st.markdown("### 🧱 Select Tile Combination")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            tile_type_options = df_current_stock["tile_type"].unique() if not df_current_stock.empty else []
            tile_type = st.selectbox("Tile Type", tile_type_options)
        with col2:
            subtype_options = df_current_stock[df_current_stock["tile_type"] == tile_type]["interlock_subtype"].unique() if not df_current_stock.empty else []
            interlock_subtype = st.selectbox("Subtype", subtype_options)
        with col3:
            size_options = df_current_stock[
                (df_current_stock["tile_type"] == tile_type) & (df_current_stock["interlock_subtype"] == interlock_subtype)
            ]["interlock_size"].unique() if not df_current_stock.empty else []
            interlock_size = st.selectbox("Size", size_options)
        with col4:
            color_options = df_current_stock[
                (df_current_stock["tile_type"] == tile_type) &
                (df_current_stock["interlock_subtype"] == interlock_subtype) &
                (df_current_stock["interlock_size"] == interlock_size)
            ]["color"].unique() if not df_current_stock.empty else []
            color = st.selectbox("Color", color_options)

        available_row = df_current_stock[
            (df_current_stock["tile_type"] == tile_type) &
            (df_current_stock["interlock_subtype"] == interlock_subtype) &
            (df_current_stock["interlock_size"] == interlock_size) &
            (df_current_stock["color"] == color)
        ]
        available_qty = int(available_row["available_qty"].values[0]) if not available_row.empty else 0

        st.info(f"📦 Available Stock: **{available_qty}**")

        col1, col2, col3 = st.columns(3)
        with col1:
            qty = st.number_input("Quantity", min_value=0, step=1, key="qty_input")
        with col2:
            price = st.number_input("Price per Tile (₹)", min_value=0.0, step=0.5, key="price_input")
        with col3:
            total_amt = qty * price
            st.markdown(f"### 💵 Amount: ₹ {total_amt:,.2f}")

        if st.button("➕ Add Item to Cart", use_container_width=True):
            if qty <= 0:
                st.error("⚠️ Quantity should be greater than 0")
            elif qty > available_qty:
                st.error(f"❌ Sale quantity ({qty}) cannot exceed available stock ({available_qty})")
            else:
                st.session_state.cart.append({
                    "tile_type": tile_type,
                    "interlock_subtype": interlock_subtype,
                    "interlock_size": interlock_size,
                    "color": color,
                    "qty": qty,
                    "price": price,
                    "amount": total_amt
                })
                st.success("✅ Item added to cart")

        # Cart section
        if st.session_state.cart:
            st.markdown("### 🛒 Cart Items")
            df_cart = pd.DataFrame(st.session_state.cart)
            st.dataframe(df_cart, use_container_width=True)

            col1, col2 = st.columns([2, 1])
            with col1:
                payment_mode = st.selectbox("Payment Mode", ["Cash", "Online", "Wozum"])
            with col2:
                grand_total = df_cart["amount"].sum()
                st.markdown(f"### 💰 Total: ₹ {grand_total:,.2f}")

            if st.button("✅ Confirm Sale", use_container_width=True):
                if not customer_name.strip():
                    st.error("❌ Customer name cannot be empty")
                elif not st.session_state.cart:
                    st.error("❌ Cart is empty")
                else:
                    sale_id = str(uuid.uuid4())
                    for item in st.session_state.cart:
                        tile_name = f"{item['tile_type']} {item['interlock_subtype']} {item['interlock_size']} {item['color']}".replace(" - -", "")
                        cur.execute("""
                            INSERT INTO sale (
                                sale_id, customer_name, customer_phone_number, tile_type, quantity, price_per_tile, amount, payment_mode, date
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            sale_id,
                            customer_name,
                            customer_phone,
                            tile_name,
                            item["qty"],
                            item["price"],
                            item["amount"],
                            payment_mode,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        ))
                    conn.commit()
                    st.success(f"✅ Sale recorded for {customer_name}")
                    st.session_state.cart = []

    # ------------------------ CURRENT AVAILABLE STOCK ------------------------
    st.markdown("## 📦Available Stock")

    def color_stock(val):
        if val <= 0:
            return "background-color: #f8d7da; color: #721c24; font-weight: bold;"  # Red = out of stock
        elif val < 50:
            return "background-color: #fff3cd; color: #856404;"  # Amber = low stock
        else:
            return "background-color: #d4edda; color: #155724;"  # Green = healthy stock

    styled_stock = df_current_stock.style.format({
        "available_qty": "{:,.0f}",
        "quantity": "{:,.0f}"
    }).applymap(color_stock, subset=["available_qty"])

    st.dataframe(styled_stock, use_container_width=True)


    # ------------------------ GROUPED SALES TABLE ------------------------
    st.markdown("## 📋Sales Records")

    if not df_sales.empty:
        grouped_sales = df_sales.groupby("sale_id").apply(
            lambda x: pd.Series({
                "Customer": x["customer_name"].iloc[0],
                "Phone": x["customer_phone_number"].iloc[0],
                "Tiles": ", ".join([
                    f"{row['tile_type_parsed']} {row['interlock_subtype']} {row['interlock_size']} {row['color']} "
                    f"x{row['quantity']} @₹{row['price_per_tile']}"
                    for idx, row in x.iterrows()
                ]),
                "Total Qty": x["quantity"].sum(),
                "Total Amount (₹)": x["amount"].sum(),
                "Payment": x["payment_mode"].iloc[0],
                "Date": pd.to_datetime(x["date"].iloc[0]).strftime("%d-%b-%Y %I:%M %p")
            })
        ).reset_index(drop=True)

        def color_amount(val):
            if val > 5000:
                return "background-color: #d4edda; color: #155724; font-weight: bold;"  # High = green
            elif val > 1000:
                return "background-color: #fff3cd; color: #856404;"  # Medium = amber
            else:
                return "background-color: #f8d7da; color: #721c24;"  # Low = red

        styled_sales = grouped_sales.style.format({
            "Total Amount (₹)": "₹{:,.2f}",
            "Total Qty": "{:,.0f}"
        }).applymap(color_amount, subset=["Total Amount (₹)"])

        st.dataframe(styled_sales, use_container_width=True)
    else:
        st.info("ℹ️ No sales recorded yet.")

# ---------------- TAB 2: Invoice Generator ----------------
with tab2:
    # --- Code from invoice.py goes here ---
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

