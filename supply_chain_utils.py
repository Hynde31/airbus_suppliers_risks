from suppliers_data import SUPPLIERS
from geo_risk_index import GEO_RISK_INDEX
import pandas as pd

def enrich_suppliers_with_risk():
    rows = []
    for supplier in SUPPLIERS:
        for site in supplier['sites']:
            risk = GEO_RISK_INDEX.get(site['country'], 50)
            dual = supplier.get("dual_sourcing", False)
            lead_pred = predict_lead_time(site['lead_time'], risk, dual)
            stockout = site['stock_days'] - lead_pred
            rows.append({
                "Supplier": supplier['name'],
                "Component": supplier['component'],
                "Criticality": supplier['criticality'],
                "Dual Sourcing": dual,
                "Site": f"{site['city']}, {site['country']}",
                "Latitude": site['lat'],
                "Longitude": site['lon'],
                "Stock Days": site['stock_days'],
                "Base Lead Time": site['lead_time'],
                "Geo Risk": risk,
                "Predicted Lead Time": lead_pred,
                "Days to Stockout": stockout,
                "Alert": "Rupture probable" if stockout < 0 else "",
            })
    return pd.DataFrame(rows)

def predict_lead_time(base_lead_time, geo_risk, dual_sourcing):
    # Modèle simple : lead time augmente avec le risque et l'absence de dual sourcing
    multiplier = 1 + (geo_risk / 100) * 0.6 + (0.3 if not dual_sourcing else 0)
    return int(base_lead_time * multiplier)

def simulate_scenario(df, event):
    # event = {"country": "Maroc", "delta_risk": 50}
    df.loc[df['Site'].str.contains(event["country"]), "Geo Risk"] += event["delta_risk"]
    df["Predicted Lead Time"] = df.apply(
        lambda row: predict_lead_time(row["Base Lead Time"], row["Geo Risk"], row["Dual Sourcing"]),
        axis=1
    )
    df["Days to Stockout"] = df["Stock Days"] - df["Predicted Lead Time"]
    df["Alert"] = df["Days to Stockout"].apply(lambda x: "Rupture probable" if x < 0 else "")
    return df