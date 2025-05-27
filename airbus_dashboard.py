import pandas as pd
from suppliers_data import SUPPLIERS

def flatten_suppliers(suppliers):
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
                "latitude": site["lat"],     # IMPORTANT: colonne nommée latitude
                "longitude": site["lon"],    # IMPORTANT: colonne nommée longitude
                "Stock Days": site["stock_days"],
                "Lead Time": site["lead_time"],
                "On-Time Delivery": site.get("on_time_delivery", None),
                "Incidents": site.get("incidents", None)
            })
    return pd.DataFrame(rows)

# Exemple d'utilisation
df = flatten_suppliers(SUPPLIERS)
print(df.head())

# Pour la carte Streamlit :
import streamlit as st
st.map(df[["latitude", "longitude"]])

import streamlit as st
import pandas as pd
from supply_chain_utils import enrich_suppliers_with_risk, simulate_scenario

st.set_page_config(layout="wide", page_title="Airbus Supply Chain Risk Dashboard")

st.title("🔴 Airbus Supply Chain Risk Dashboard - IA & Géopolitique")

df = enrich_suppliers_with_risk()
scenarios = [
    {"label": "Aucun", "country": None, "delta_risk": 0},
    {"label": "Embargo Maroc", "country": "Maroc", "delta_risk": 40},
    {"label": "Grève France", "country": "France", "delta_risk": 25},
    {"label": "Tensions USA", "country": "USA", "delta_risk": 30},
    # Ajoute d'autres scénarios selon l'actualité
]

# Simulation de scénario
scenario = st.sidebar.selectbox("Simulation géopolitique", [s["label"] for s in scenarios])
chosen = next((s for s in scenarios if s["label"] == scenario), scenarios[0])

if chosen["country"]:
    df = simulate_scenario(df, chosen)

# KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Fournisseurs à risque élevé", len(df[df["Geo Risk"] > 35]))
col2.metric("Ruptures probables", len(df[df["Alert"] != ""]))
col3.metric("Lead time moyen prédit", int(df["Predicted Lead Time"].mean()))
col4.metric("Stock moyen (jours)", int(df["Stock Days"].mean()))

# Carte des sites
st.subheader("Carte mondiale des fournisseurs (couleur = risque géopolitique)")
st.map(df.rename(columns={"Latitude": "lat", "Longitude": "lon"}))

# Tableau principal
st.subheader("Détail par site/fournisseur")
st.dataframe(df, use_container_width=True)

# Alertes et recommandations IA
if df["Alert"].str.contains("Rupture").any():
    st.warning("⚠️ Risque de rupture détecté !\n\nActions IA recommandées :")
    for _, row in df[df["Alert"] == "Rupture probable"].iterrows():
        st.markdown(f"- **{row['Supplier']} ({row['Site']})** : Activer sourcing alternatif, augmenter stock, prioriser expéditions, revoir plan de production.")

# Export rapport
if st.button("Exporter données (CSV)"):
    st.download_button("Télécharger", df.to_csv(index=False), "supply_chain_report.csv")
