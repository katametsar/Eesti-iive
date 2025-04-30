import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import requests
import json
from io import StringIO

st.set_page_config(layout="wide")
st.title("👶 Loomulik iive Eestis")

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
geojson = "maakonnad.geojson"

JSON_PAYLOAD_STR = """{
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": ["2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023"]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": ["39", "44", "49", "70", "51", "57", "59", "65", "67", "74", "78", "82", "84","37", "86"]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": ["2", "3"]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}"""

def import_data():
    headers = {"Content-Type": "application/json"}
    response = requests.post(STATISTIKAAMETI_API_URL, json=json.loads(JSON_PAYLOAD_STR), headers=headers)
    if response.status_code == 200:
        df = pd.read_csv(StringIO(response.content.decode('utf-8-sig')))
        return df
    else:
        st.error("Andmete laadimine ebaõnnestus")
        return pd.DataFrame()

def import_geojson():
    gdf = gpd.read_file(geojson)
    return gdf

# Load data
df = import_data()
gdf = import_geojson()

# --- Sidebar filters ---
st.sidebar.header("🎛️ Filtrid")

aastad = sorted(df["Aasta"].unique())
maakonnad = sorted(df["Maakond"].unique())
sugude_valikud = {
    "Mehed": "Mehed Loomulik iive",
    "Naised": "Naised Loomulik iive",
    "Kokku": "KOKKU"
}

valitud_aasta = st.sidebar.selectbox("Vali aasta", aastad, index=len(aastad)-1)
valitud_sugu = st.sidebar.selectbox("Vali sugu", list(sugude_valikud.keys()))
valitud_maakond = st.sidebar.selectbox("Vali maakond", ["Kõik"] + maakonnad)

# Calculate "Loomulik iive"
if valitud_sugu == "Kokku":
    df["Loomulik iive"] = df["Mehed Loomulik iive"] + df["Naised Loomulik iive"]
else:
    df["Loomulik iive"] = df[sugude_valikud[valitud_sugu]]

# Filter data
df_filtered = df[df["Aasta"] == valitud_aasta]
if valitud_maakond != "Kõik":
    df_filtered = df_filtered[df_filtered["Maakond"] == valitud_maakond]

# Merge with geodata (Now after filtering)
merged = gdf.merge(df_filtered, left_on="MNIMI", right_on="Maakond", how="inner")

# Show warning if join failed
if merged.empty:
    st.warning("❌ Andmeid ei leitud valitud kriteeriumite põhjal.")
else:
    # Plot if data is valid
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    merged.plot(
        column="Loomulik iive",
        ax=ax,
        legend=True,
        cmap="YlGnBu",
        edgecolor="white",
        linewidth=0.5,
        legend_kwds={"label": "Loomulik iive", "orientation": "horizontal"}
    )
    ax.set_title(f"Loomulik iive maakonniti – {valitud_aasta}", fontsize=14)
    ax.axis("off")
    st.pyplot(fig) 

# --- Statistics ---
st.subheader(f"📊 {valitud_aasta} Statistika – {valitud_sugu.lower()}")
col1, col2, col3 = st.columns(3)
col1.metric("Keskmine", f"{merged['Loomulik iive'].mean():.2f}")
col2.metric("Maksimaalne", f"{merged['Loomulik iive'].max()}")
col3.metric("Minimaalne", f"{merged['Loomulik iive'].min()}")
