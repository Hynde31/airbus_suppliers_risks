import streamlit as st
import pandas as pd
import numpy as np
import os
from suppliers_data import SUPPLIERS

st.set_page_config(page_title="Airbus Suppliers Risk Dashboard", layout="wide")

# --------- DATA FLATTENING ---------
def flatten_suppliers(suppliers):
    rows = []
    for s in suppliers:
        for site in s["sites"]:
            rows.append({
                "Supplier": s["name"],
                "Component": s["component"],
                "Criticality": s["criticality"],
                "Dual Sourcing": "Yes" if s["dual_sourcing"] else "No",
                "Site City": site["city"],
                "Site Country": site["country"],
                "Latitude": site["lat"],
                "Longitude": site["lon"],
                "Stock Days": site["stock_days"],
                "Lead Time": site["lead_time"],
                "On-Time Delivery Rate (%)": site.get("on_time_delivery", 90),
                "Incident Rate (/year)": site.get("incidents", 1)
            })
    return pd.DataFrame(rows)

df = flatten_suppliers(SUPPLIERS)

# --- ADDITIONAL KPI DERIVED COLUMNS ---
df["Risk Score"] = (1 - df["On-Time Delivery Rate (%)"]/100) \
                   + (df["Incident Rate (/year)"]/10) \
                   + (1 - df["Stock Days"]/60)*0.5 \
                   + (df["Lead Time"]/150)*0.5
df["Risk Level"] = pd.cut(df["Risk Score"], bins=[-np.inf,0.5,1,2], labels=["Low","Medium","High"])

# --- Harmonize column names for filters and charts
df = df.rename(columns={
    "Site Country": "Country",
    "Incident Rate (/year)": "Incidents",
    "On-Time Delivery Rate (%)": "On-Time Delivery (%)"
})

# --------- STREAMLIT APP SETUP ---------
st.title("Airbus Suppliers Risk Dashboard")

# Affichage du logo si présent
logo_path = "airbus_logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=180)

# --------- SIDEBAR: SCENARIO & FILTERS ---------
st.sidebar.header("Scenario Simulation & Filters")
scenario = st.sidebar.selectbox(
    'Geopolitical Scenario Simulation',
    ['None', 'Embargo', 'Strike', 'War']
)
impact = st.sidebar.slider('News impact on risk (adds to "Incidents"):', 0, 5, 0)
selected_criticality = st.sidebar.multiselect(
    "Criticality", options=sorted(df["Criticality"].unique()), default=list(df["Criticality"].unique()))
selected_country = st.sidebar.multiselect(
    "Country", options=sorted(df["Country"].unique()), default=list(df["Country"].unique()))
selected_component = st.sidebar.multiselect(
    "Component", options=sorted(df["Component"].unique()), default=list(df["Component"].unique()))

# Apply scenario impact
df_scenar = df.copy()
if scenario == "Embargo":
    df_scenar["Lead Time"] += 15
    df_scenar["Incidents"] = df_scenar["Incidents"].fillna(0) + 2
elif scenario == "Strike":
    df_scenar["Lead Time"] += 10
    df_scenar["Incidents"] = df_scenar["Incidents"].fillna(0) + 3
elif scenario == "War":
    df_scenar["Lead Time"] += 30
    df_scenar["Incidents"] = df_scenar["Incidents"].fillna(0) + 6
if impact:
    df_scenar["Incidents"] = df_scenar["Incidents"].fillna(0) + impact

# Filtered data
filtered_df = df_scenar[
    df_scenar["Criticality"].isin(selected_criticality)
    & df_scenar["Country"].isin(selected_country)
    & df_scenar["Component"].isin(selected_component)
]

# --------- MAP OF SUPPLIER SITES ---------
st.subheader("Supplier Sites Map")
if not filtered_df.empty and "Latitude" in filtered_df.columns and "Longitude" in filtered_df.columns:
    st.map(filtered_df[["Latitude", "Longitude"]])
else:
    st.info("No supplier sites match your filters or missing coordinates.")

# --------- SUPPLIERS TABLE ---------
st.subheader("Suppliers Table")
st.dataframe(filtered_df, use_container_width=True)

# --------- GLOBAL STATISTICS ---------
st.subheader("Global Statistics")
col1, col2, col3 = st.columns(3)
col1.metric("Unique Suppliers", filtered_df["Supplier"].nunique())
col2.metric("Countries", filtered_df["Country"].nunique())
col3.metric("Total Incidents", int(filtered_df["Incidents"].sum() if filtered_df["Incidents"].notnull().any() else 0))

# --------- RISK & PERFORMANCE OVERVIEW ---------
st.subheader("Risk and Performance Overview")
col4, col5 = st.columns(2)
with col4:
    st.bar_chart(filtered_df.groupby("Supplier")["Incidents"].sum())
with col5:
    st.bar_chart(filtered_df.groupby("Country")["On-Time Delivery (%)"].mean())

# --------- SUPPLIER DETAILS ---------
st.subheader("Supplier Details")
suppliers = filtered_df["Supplier"].unique()
if len(suppliers) > 0:
    selected_supplier = st.selectbox("Select a supplier for details", suppliers)
    supplier_details = filtered_df[filtered_df["Supplier"] == selected_supplier]
    st.write(supplier_details)

    # Recommendations based on incidents and stock
    high_incidents = supplier_details["Incidents"].max() >= 5
    low_stock = supplier_details["Stock Days"].min() <= 10
    st.markdown("**AI Recommendations:**")
    if high_incidents and low_stock:
        st.warning("🚨 High incident rate and low stock: consider dual sourcing and increase safety stock level.")
    elif high_incidents:
        st.warning("⚠️ High incident rate: increase monitoring, plan audits, and consider alternative suppliers.")
    elif low_stock:
        st.info("🔎 Low stock: consider increasing safety stock.")
    else:
        st.success("✅ No major risk detected for this supplier right now.")

    # Export to Excel feature
    import io
    excel_buffer = io.BytesIO()
    supplier_details.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    st.download_button(
        label="Download Excel file",
        data=excel_buffer,
        file_name=f"{selected_supplier}_details.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("No supplier selected.")

# --------- FOOTER ---------
st.markdown("""
---
Developed for Airbus - Supply Chain Digital Twin · [2025]
""")
