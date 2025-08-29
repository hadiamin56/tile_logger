import streamlit as st
import pandas as pd
from db import get_conn

st.set_page_config(page_title="Labour Payments Dashboard", layout="wide")
st.title("🧾 Labour Payments Dashboard")

conn = get_conn()
cursor = conn.cursor()

# --- Calculate totals ---
cursor.execute("SELECT SUM(labour_charges) FROM daily_log")
total_charges = cursor.fetchone()[0] or 0.0   # includes loading also

cursor.execute("SELECT SUM(amount) FROM labour_payments")
total_paid = cursor.fetchone()[0] or 0.0      # only real cash payments

balance = total_charges - total_paid

# --- Summary cards ---
col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Charges", f"₹ {total_charges:,.2f}")
col2.metric("💵 Total Paid", f"₹ {total_paid:,.2f}")
col3.metric("⚖️ Balance", f"₹ {balance:,.2f}")

st.markdown("---")

# --- Add new payment form ---
with st.expander("Add New Payment"):
    payment_date = st.date_input("Payment Date")
    amount = st.number_input("Amount Paid", min_value=0.0, value=0.0)
    purpose = st.text_input("Purpose (optional)")
    
    if st.button("Add Payment"):
        cursor.execute(
            "INSERT INTO labour_payments(date, amount, purpose) VALUES(?,?,?)",
            (str(payment_date), amount, purpose)
        )
        conn.commit()
        st.success(f"Payment of ₹ {amount:,.2f} added!")

st.markdown("---")

# --- Display all payments ---
st.subheader("📋 Payment History")
df_payments = pd.read_sql("SELECT * FROM labour_payments ORDER BY date DESC", conn)
st.dataframe(df_payments, use_container_width=True)

conn.close()
