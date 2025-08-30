import streamlit as st
import pandas as pd
from db import get_conn

st.set_page_config(page_title="Labour Charges Config", layout="wide")
st.title("⚙️ Labour Charges Configuration")

conn = get_conn()

# --- Fetch config data ---
df_config = pd.read_sql("SELECT * FROM config", conn)

# --- Show existing config ---
st.subheader("📋 Current Labour Charges")
st.dataframe(df_config, use_container_width=True)

st.markdown("---")
st.subheader("✏️ Update Existing Charges")

# --- Update form ---
if not df_config.empty:
    cols = st.columns(len(df_config))
    new_values = {}
    for i, row in df_config.iterrows():
        with cols[i]:
            label = f"{row['category']} - {row['option_name']}"
            new_val = st.number_input(
                label,
                value=row['value'],
                min_value=0.0,
                step=0.5,
                key=f"update_{row['id']}"
            )
            new_values[row['id']] = new_val

    if st.button("💾 Update Charges"):
        for id_, val in new_values.items():
            conn.execute("UPDATE config SET value=? WHERE id=?", (val, id_))
        conn.commit()
        st.success("✅ Charges updated successfully!")
        st.rerun()
else:
    st.info("⚠️ No labour charges configured yet. Add one below.")

# --- Add new config option ---
st.markdown("---")
st.subheader("➕ Add New Labour Charge")

with st.form("add_config_form"):
    category = st.text_input("Category (e.g. Tile, Interlock)")
    option_name = st.text_input("Option Name (e.g. 1x1, 60mm)")
    value = st.number_input("Charge Value", min_value=0.0, step=0.5)
    submitted = st.form_submit_button("➕ Add")
    if submitted:
        if category.strip() == "" or option_name.strip() == "":
            st.error("❌ Both Category and Option Name are required!")
        else:
            conn.execute(
                "INSERT INTO config (category, option_name, value) VALUES (?, ?, ?)",
                (category, option_name, value)
            )
            conn.commit()
            st.success(f"✅ Added new charge: {category} - {option_name} = {value}")
            st.rerun()

# --- Delete config option ---
st.markdown("---")
st.subheader("🗑️ Delete Labour Charge")

if not df_config.empty:
    delete_id = st.selectbox(
        "Select config option to delete",
        options=df_config['id'],
        format_func=lambda x: f"{df_config.loc[df_config['id']==x, 'category'].values[0]} - {df_config.loc[df_config['id']==x, 'option_name'].values[0]}"
    )
    if st.button("🗑️ Delete Selected Option"):
        conn.execute("DELETE FROM config WHERE id=?", (delete_id,))
        conn.commit()
        st.success("✅ Config option deleted!")
        st.rerun()
else:
    st.info("⚠️ No config available to delete.")

conn.close()
