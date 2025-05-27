import streamlit as st
import pandas as pd
from suppliers_data import SUPPLIERS

# --------- DATA FLATTENING ---------
def flatten_suppliers(suppliers):
    """
    Transforme la structure SUPPLIERS (liste de dicts imbriqués) en DataFrame plat,
    avec latitude/longitude pour affichage Streamlit et tous les champs utiles.
    """
    rows = []
    for s in suppliers:
        for site in s["sites"]:
            rows.append({
                "Supplier": s["name"],
                "Component": s["component"],
                "Criticality": s["criticality"],
                "Dual Sourcing": "Yes" if s["dual_sourcing"] else "No",
                "City": site["city"],
                "Country": site["country"],
                "latitude": site["lat"],
                "longitude": site["lon"],
                "Stock Days": site["stock_days"],
                "Lead Time": site["lead_time"],
                "On-Time Delivery (%)": site.get("on_time_delivery", None),
                "Incidents": site.get("incidents", None)
            })
    return pd.DataFrame(rows)

df = flatten_suppliers(SUPPLIERS)

# --------- STREAMLIT APP ---------
st.set_page_config(page_title="Airbus Suppliers Risk Dashboard", layout="wide")
st.title("Airbus Suppliers Risk Dashboard")

# Affichage du logo si présent
import os
logo_path = "airbus_logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=180)

# Sidebar - Filtres interactifs
st.sidebar.header("Filters")
selected_criticality = st.sidebar.multiselect(
    "Criticality", options=sorted(df["Criticality"].unique()), default=list(df["Criticality"].unique()))
selected_country = st.sidebar.multiselect(
    "Country", options=sorted(df["Country"].unique()), default=list(df["Country"].unique()))
selected_component = st.sidebar.multiselect(
    "Component", options=sorted(df["Component"].unique()), default=list(df["Component"].unique()))

filtered_df = df[
    df["Criticality"].isin(selected_criticality)
    & df["Country"].isin(selected_country)
    & df["Component"].isin(selected_component)
]

# Carte des sites fournisseurs
st.subheader("Supplier Sites Map")
if not filtered_df.empty and "latitude" in filtered_df.columns and "longitude" in filtered_df.columns:
    st.map(filtered_df[["latitude", "longitude"]])
else:
    st.info("No supplier sites match your filters or missing coordinates.")

# Tableau des fournisseurs
st.subheader("Suppliers Table")
st.dataframe(filtered_df, use_container_width=True)

# Statistiques globales
st.subheader("Global Statistics")
col1, col2, col3 = st.columns(3)
col1.metric("Unique Suppliers", filtered_df["Supplier"].nunique())
col2.metric("Countries", filtered_df["Country"].nunique())
col3.metric("Total Incidents", int(filtered_df["Incidents"].sum() if filtered_df["Incidents"].notnull().any() else 0))

# Graphiques de synthèse
st.subheader("Risk and Performance Overview")
col4, col5 = st.columns(2)
with col4:
    st.bar_chart(filtered_df.groupby("Supplier")["Incidents"].sum())
with col5:
    st.bar_chart(filtered_df.groupby("Country")["On-Time Delivery (%)"].mean())

# Détail par fournisseur
st.subheader("Supplier Details")
suppliers = filtered_df["Supplier"].unique()
if len(suppliers) > 0:
    selected_supplier = st.selectbox("Select a supplier for details", suppliers)
    supplier_details = filtered_df[filtered_df["Supplier"] == selected_supplier]
    st.write(supplier_details)
else:
    st.info("No supplier selected.")

st.markdown("""
