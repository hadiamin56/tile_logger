import streamlit as st
import pandas as pd
from db import get_conn

st.set_page_config(page_title="Labour Charges Config", layout="wide")
st.title("⚙️ Labour Charges Configuration")

conn = get_conn()
df_config = pd.read_sql("SELECT * FROM config", conn)

# --- Display current config as table ---
st.subheader("Current Labour Charges")
st.dataframe(df_config, use_container_width=True)

st.markdown("---")
st.subheader("Update Labour Charges")

# --- Update form in columns ---
cols = st.columns(len(df_config))
new_values = {}

for i, row in df_config.iterrows():
    with cols[i]:
        new_val = st.number_input(
            f"{row['name'].capitalize()} charge",
            value=row['value'],
            min_value=0.0,
            step=0.5,
            key=row['id']
        )
        new_values[row['id']] = new_val

if st.button("Update Charges"):
    for id_, val in new_values.items():
        conn.execute("UPDATE config SET value=? WHERE id=?", (val, id_))
    conn.commit()
    st.success("✅ Labour charges updated successfully!")

conn.close()
