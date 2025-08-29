import streamlit as st
from PIL import Image
from db import init_db, get_conn
import pandas as pd

# Initialize DB
init_db()

st.set_page_config(
    page_title="Seeloo Tile Factory",
    page_icon="🏭",
    layout="wide"
)

# --- Branding & Welcome Section ---
st.markdown("""
    <div style='text-align:center'>
        <h1 style='color:#2F4F4F'>🏭 Seeloo Tile Factory</h1>
        <h3 style='color:#555555'>Floor Tiles & Flower Pots</h3>
        <p style='color:#777777'>Seeloo, Sopore | Premium quality tiles & pots</p>
    </div>
""", unsafe_allow_html=True)

# Optional: add an image banner if you have one
try:
    banner = Image.open("assets/banner.jpg")  # Replace with your image path
    st.image(banner, use_column_width=True)
except:
    pass


# --- Quick Stats ---
conn = get_conn()
cursor = conn.cursor()




# --- Navigation Buttons to Pages ---
col1, col2, col3, col4 = st.columns(4)
col1.button("📋 Daily Logs")
    # st.experimental_set_query_params(page="DAILY_LOG")
col2.button("💵 Labour Payments")
    # st.experimental_set_query_params(page="LABOUR_PAYMENTS")
col3.button("🧾 Material Expenses")
    # st.experimental_set_query_params(page="RAW_MATERIALS")
col4.button("📊 Dashboard")
    # st.experimental_set_query_params(page="DASHBOARD")

st.markdown("<div style='text-align:center;color:#888;'>© 2025 Seeloo Tile Factory, Sopore</div>", unsafe_allow_html=True)

conn.close()
