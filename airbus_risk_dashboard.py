import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
import os

# -----------------------------
# DATA LOADING (to be replaced by DB or API in prod)
from suppliers_data import SUPPLIERS

# --- DATAFRAME CREATION ---
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
                "Lead Time": site["lead_time"]
            })
    return pd.DataFrame(rows)

df = flatten_suppliers(SUPPLIERS)

# --- ADDITIONAL KPI DERIVED COLUMNS ---
np.random.seed(42)
df["On-Time Delivery Rate (%)"] = np.random.randint(70, 99, size=len(df))
df["Incident Rate (/year)"] = np.random.randint(0, 7, size=len(df))
df["Risk Score"] = (1 - df["On-Time Delivery Rate (%)"]/100) \
                   + (df["Incident Rate (/year)"]/10) \
                   + (1 - df["Stock Days"]/60)*0.5 \
                   + (df["Lead Time"]/150)*0.5
df["Risk Level"] = pd.cut(df["Risk Score"], bins=[-np.inf,0.5,1,2], labels=["Low","Medium","High"])

# --- PREDICTIVE AI: STOCK-OUT PREDICTION ---
@st.cache_data
def train_predictive_model(df):
    X = df[["Stock Days","Lead Time","On-Time Delivery Rate (%)","Incident Rate (/year)"]]
    y = (df["Lead Time"]*1.5 - df["Stock Days"]).clip(lower=0) + np.random.normal(0,3,len(df))
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

model = train_predictive_model(df)

def predict_stockout(row):
    features = row[["Stock Days","Lead Time","On-Time Delivery Rate (%)","Incident Rate (/year)"]].values.reshape(1, -1)
    pred = model.predict(features)[0]
    return round(pred, 1)

df["Predicted Stock-Out Risk (days)"] = df.apply(predict_stockout, axis=1)

# --- STREAMLIT UI ---
st.set_page_config(page_title="Airbus Digital Twin Supply Chain Dashboard", layout="wide")
st.title("Airbus Supply Chain Digital Twin Dashboard")

with st.sidebar:
    st.header("Simulation & Filters")
    country = st.selectbox("Filter by country", ["All"] + sorted(df["Site Country"].unique().tolist()))
    crit = st.selectbox("Filter by criticality", ["All"] + sorted(df["Criticality"].unique().tolist()))
    dual = st.selectbox("Dual sourcing", ["All", "Yes", "No"])
    rf = st.slider("Global Risk Amplifier (scenario)", 0.5, 2.0, 1.0, 0.05)
    st.markdown("*Use the sliders to simulate scenario stress (embargo, strike, war, etc)*")
    show_map = st.checkbox("Show map", True)

# --- FILTERING ---
filtered = df.copy()
if country != "All":
    filtered = filtered[filtered["Site Country"]==country]
if crit != "All":
    filtered = filtered[filtered["Criticality"]==crit]
if dual != "All":
    filtered = filtered[filtered["Dual Sourcing"]==dual]
if rf != 1.0:
    filtered["Risk Score"] *= rf
    filtered["Predicted Stock-Out Risk (days)"] *= rf
    filtered["Risk Level"] = pd.cut(filtered["Risk Score"], bins=[-np.inf,0.5,1,2], labels=["Low","Medium","High"])

# --- MAP VISUALIZATION ---
if show_map:
    st.subheader("Supplier Sites Geolocation (color by risk level)")
    map_data = filtered[["Latitude","Longitude"]].copy()
    st.map(map_data)

# --- KPI BOARD ---
st.subheader("Supplier Site Details")
site = st.selectbox("Select a supplier site", filtered.index, format_func=lambda i: f"{filtered.loc[i,'Supplier']} ({filtered.loc[i,'Site City']}, {filtered.loc[i,'Site Country']})")
site_row = filtered.loc[site]

st.markdown(f"""
- **Supplier:** {site_row['Supplier']}
- **Component:** {site_row['Component']}
- **Criticality:** {site_row['Criticality']}
- **Dual Sourcing:** {site_row['Dual Sourcing']}
- **City/Country:** {site_row['Site City']} / {site_row['Site Country']}
- **On-Time Delivery Rate:** {site_row['On-Time Delivery Rate (%)']} %
- **Incident Rate:** {site_row['Incident Rate (/year)']}
- **Stock Coverage:** {site_row['Stock Days']} days
- **Lead Time:** {site_row['Lead Time']} days
- **Current Risk Score:** {site_row['Risk Score']:.2f} ({site_row['Risk Level']})
- :robot_face: **Predicted Stock-Out Risk:** {site_row['Predicted Stock-Out Risk (days)']} days
""")

# --- AI RECOMMENDATIONS ---
def ai_recommendations(site_row):
    recs = []
    if site_row["Predicted Stock-Out Risk (days)"] < 10:
        recs.append("⚠️ Increase safety stock or source alternative suppliers urgently.")
    elif site_row["Risk Level"]=="High":
        recs.append("🚨 Conduct deep audit and risk mitigation plan. Consider dual sourcing.")
    elif site_row["Risk Level"]=="Medium":
        recs.append("Monitor supplier performance and schedule regular reviews.")
    else:
        recs.append("No immediate action required. Maintain current relationship.")
    return recs

st.info("**AI Recommendations:**\n\n" + "\n".join(ai_recommendations(site_row)))

# --- DATA VISUALIZATION ---
st.subheader("Comparative Dashboard")
cols = st.columns(4)
for idx, col in enumerate(cols):
    if idx==0:
        col.bar_chart(filtered.set_index("Supplier")["Risk Score"])
    elif idx==1:
        col.line_chart(filtered.set_index("Supplier")["Predicted Stock-Out Risk (days)"])
    elif idx==2:
        col.area_chart(filtered.set_index("Supplier")["Stock Days"])
    elif idx==3:
        col.line_chart(filtered.set_index("Supplier")["Incident Rate (/year)"])

# --- EXPORT REPORT ---
def export_pptx(site_row, logo_path='airbus_logo.png'):
    prs = Presentation()
    slide_layout = prs.slide_layouts[5]
    slide = prs.slides.add_slide(slide_layout)
    if slide.shapes.title:
        slide.shapes.title.text = "Supplier Digital Twin Risk Report"

    if os.path.exists(logo_path):
        slide.shapes.add_picture(logo_path, Inches(0.5), Inches(0.5), height=Inches(1.0))
    left, top, width, height = Inches(0.5), Inches(1.8), Inches(8.5), Inches(4)
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame; tf.word_wrap = True
    lines = [
        f"Supplier: {site_row['Supplier']}",
        f"Component: {site_row['Component']}",
        f"Criticality: {site_row['Criticality']}",
        f"Dual Sourcing: {site_row['Dual Sourcing']}",
        f"Country: {site_row['Site Country']}",
        f"City: {site_row['Site City']}",
        f"On-Time Delivery Rate: {site_row['On-Time Delivery Rate (%)']}%",
        f"Incident Rate: {site_row['Incident Rate (/year)']}",
        f"Stock Coverage: {site_row['Stock Days']} days",
        f"Lead Time: {site_row['Lead Time']} days",
        f"Risk Score: {site_row['Risk Score']:.2f} ({site_row['Risk Level']})",
        f"Predicted Stock-Out Risk (AI): {site_row['Predicted Stock-Out Risk (days)']} days",
        "",
        "AI Recommendations:",
        *ai_recommendations(site_row)
    ]
    for line in lines:
        p = tf.add_paragraph(); p.text = line; p.font.size = Pt(16 if ":" in line else 14)
        if "AI Recommendations" in line: p.font.bold = True
        if line.startswith("⚠️") or line.startswith("🚨"): p.font.bold = True

    prs.save('supplier_digital_twin_report.pptx')
    st.success('PowerPoint report generated successfully!')

if st.button("Export PowerPoint Report"):
    export_pptx(site_row)