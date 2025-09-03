import streamlit as st

# Create tabs for the two apps
tab1, tab2 = st.tabs(["Daily Log", "Labour Payments"])

# ---------------- TAB 1: Sales Dashboard ----------------
with tab1:
    # --- Code from sale.py goes here ---
    import streamlit as st
    import sqlite3
    import pandas as pd
    from datetime import datetime

    # --- Labour Charges ---
    PER_TILE = 3.50
    LOADING = 0.50
    POT = 200.00

    # --- DB Setup ---
    def get_conn():
        return sqlite3.connect("data/tiles.db", check_same_thread=False)

    conn = get_conn()
    cursor = conn.cursor()

    # Create daily_log table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT,
        tile_type TEXT,
        interlock_subtype TEXT,
        interlock_size TEXT,
        color TEXT,
        quantity INTEGER,
        labour_charge REAL,
        log_date DATE
    )
    """)
    conn.commit()

    # --- Streamlit Config ---
    st.set_page_config(page_title="Daily Labour Log", layout="wide")
    st.title("📝 Daily Labour Log")

    # --- Main Category ---
    category = st.selectbox("Select Category", ["Tile", "Loading", "Pot"])

    # Initialize combos in session
    if "combos" not in st.session_state:
        st.session_state.combos = []

    # --- Tile Options ---
    if category == "Tile":
        tile_type = st.selectbox("Select Tile Type", ["1x1", "Interlock"])
        interlock_subtypes = []
        interlock_sizes = []
        if tile_type == "Interlock":
            interlock_subtypes = st.multiselect("Select Interlock Subtypes", ["Kuchwa", "Cobble Stone", "L"])
            interlock_sizes = st.multiselect("Select Interlock Sizes", ["40mm", "60mm", "80mm"])
        
        # --- Color Selection with Style ---
        colors = st.multiselect("Select Colors", ["Red", "Yellow", "Grey", "Black"])
        if colors:
            st.markdown("#### 🎨 Selected Colors:")
            color_map = {
                "Red": "background-color:red;color:white;padding:6px;border-radius:5px;",
                "Yellow": "background-color:yellow;color:black;padding:6px;border-radius:5px;",
                "Grey": "background-color:grey;color:white;padding:6px;border-radius:5px;",
                "Black": "background-color:black;color:white;padding:6px;border-radius:5px;",
            }
            cols = st.columns(len(colors))
            for i, c in enumerate(colors):
                with cols[i]:
                    st.markdown(f"<div style='{color_map[c]};text-align:center;font-weight:bold'>{c}</div>", unsafe_allow_html=True)

        # Generate combinations automatically
        st.session_state.combos = []
        if tile_type == "Interlock" and interlock_subtypes and interlock_sizes and colors:
            for subtype in interlock_subtypes:
                for size in interlock_sizes:
                    for color in colors:
                        st.session_state.combos.append({
                            "tile_type": tile_type,
                            "subtype": subtype,
                            "size": size,
                            "color": color,
                            "qty": 0,
                            "labour": PER_TILE + LOADING
                        })
        elif tile_type == "1x1" and colors:
            for color in colors:
                st.session_state.combos.append({
                    "tile_type": tile_type,
                    "subtype": "-",
                    "size": "-",
                    "color": color,
                    "qty": 0,
                    "labour": PER_TILE + LOADING
                })

    # --- Loading Option ---
    elif category == "Loading":
        qty = st.number_input("Enter quantity", min_value=0, step=1, key="loading_qty")
        st.session_state.combos = [{"tile_type": "Loading", "subtype": "-", "size": "-", "color": "-", "qty": qty, "labour": LOADING}]

    # --- Pot Option ---
    elif category == "Pot":
        qty = st.number_input("Enter quantity", min_value=0, step=1, key="pot_qty")
        st.session_state.combos = [{"tile_type": "Pot", "subtype": "-", "size": "-", "color": "-", "qty": qty, "labour": POT}]

    # --- Show Dynamic Inputs in Professional UI ---
    if st.session_state.combos:
        st.subheader("🖊️ Enter Quantities")
        for i, combo in enumerate(st.session_state.combos):
            cols = st.columns([2, 2, 2, 2, 2, 2])
            with cols[0]:
                st.text(combo['tile_type'] or category)
            with cols[1]:
                st.text(combo['subtype'])
            with cols[2]:
                st.text(combo['size'])
            with cols[3]:
                st.text(combo['color'])
            with cols[4]:
                qty = st.number_input(f"Qty {i+1}", min_value=0, step=1, key=f"qty_{i}")
                combo["qty"] = qty
            with cols[5]:
                st.text(f"{combo['labour'] * combo['qty']:.2f}")

    # --- Save Log ---
    if st.session_state.combos:
        if st.button("Save Log"):
            for combo in st.session_state.combos:
                total_labour = combo["labour"] * combo["qty"]
                cursor.execute("""
                    INSERT INTO daily_log (category, tile_type, interlock_subtype, interlock_size, color, quantity, labour_charge, log_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    category,
                    combo.get("tile_type"),
                    combo.get("subtype"),
                    combo.get("size"),
                    combo.get("color"),
                    combo.get("qty"),
                    total_labour,
                    datetime.now().date()
                ))
            conn.commit()
            st.success("✅ Log saved successfully!")
            st.session_state.combos = []

    # --- Show Today's Logs ---
    st.subheader("📊 Today's Logs")
    today = datetime.now().date()
    rows = cursor.execute("""
        SELECT category, tile_type, interlock_subtype, interlock_size, color, quantity, labour_charge, log_date
        FROM daily_log WHERE log_date=?
    """, (today,)).fetchall()

    df = pd.DataFrame(rows, columns=["Category", "Tile Type", "Subtype", "Size", "Color", "Quantity", "Labour Charge", "Date"])
    st.data_editor(df, hide_index=True)


# ---------------- TAB 2: Invoice Generator ----------------
with tab2:
    # --- Code from invoice.py goes here ---
    import streamlit as st
    import pandas as pd
    from db import get_conn

    st.set_page_config(page_title="Labour Payments Dashboard", layout="wide")
    st.title("🧾 Labour Payments Dashboard")

    # --- DB Connection ---
    conn = get_conn()
    cursor = conn.cursor()

    # --- Calculate totals from daily_log ---
    cursor.execute("SELECT SUM(labour_charge) FROM daily_log")
    total_charges = cursor.fetchone()[0] or 0.0   # includes loading also

    # --- Calculate total paid ---
    cursor.execute("SELECT SUM(amount) FROM labour_payments")
    total_paid = cursor.fetchone()[0] or 0.0      # only real cash payments

    # --- Balance ---
    balance = total_charges - total_paid

    # --- Summary cards ---
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Charges", f"₹ {total_charges:,.2f}")
    col2.metric("💵 Total Paid", f"₹ {total_paid:,.2f}")
    col3.metric("⚖️ Balance", f"₹ {balance:,.2f}")

    st.markdown("---")

    # --- Add new payment form ---
    with st.expander("➕ Add New Payment"):
        payment_date = st.date_input("Payment Date")
        amount = st.number_input("Amount Paid", min_value=0.0, value=0.0)
        purpose = st.text_input("Purpose (optional)")
        
        if st.button("Add Payment"):
            cursor.execute(
                "INSERT INTO labour_payments(date, amount, purpose) VALUES(?,?,?)",
                (str(payment_date), amount, purpose)
            )
            conn.commit()
            st.success(f"✅ Payment of ₹ {amount:,.2f} added!")

    st.markdown("---")

    # --- Display all payments ---
    st.subheader("📋 Payment History")
    df_payments = pd.read_sql("SELECT * FROM labour_payments ORDER BY date DESC", conn)
    st.dataframe(df_payments, use_container_width=True)

    conn.close()

