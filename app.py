import json
from io import StringIO

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st


STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"
GEOJSON_FILE = "maakonnad.geojson"

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
        "values": ["39", "44", "49", "51", "57", "59", "65", "67", "70", "74", "78", "82", "84", "86", "37"]
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


@st.cache_data
def import_data():
    payload = json.loads(JSON_PAYLOAD_STR)
    response = requests.post(
        STATISTIKAAMETI_API_URL,
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    text = response.content.decode("utf-8-sig")
    return pd.read_csv(StringIO(text))


@st.cache_data
def import_geojson():
    return gpd.read_file(GEOJSON_FILE)


@st.cache_data
def prepare_data():
    df = import_data()
    gdf = import_geojson()
    merged_data = gdf.merge(df, left_on="MNIMI", right_on="Maakond")
    merged_data["Loomulik iive"] = (
        merged_data["Mehed Loomulik iive"] + merged_data["Naised Loomulik iive"]
    )
    return merged_data


def get_data_for_year(df, year):
    return df[df["Aasta"] == year]


def plot_map(df, year):
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    df.plot(
        column="Loomulik iive",
        ax=ax,
        legend=True,
        cmap="viridis",
        legend_kwds={"label": "Loomulik iive"},
    )
    ax.set_title(f"Loomulik iive maakonniti aastal {year}")
    ax.axis("off")
    fig.tight_layout()
    return fig


st.set_page_config(page_title="Loomulik iive Eestis", layout="wide")

st.title("Loomulik iive Eesti maakondades")
st.write(
    "Töölaud näitab Eesti maakondade loomulikku iivet aastatel 2014-2023. "
    "Loomulik iive on elussündide ja surmade vahe."
)

merged_data = prepare_data()
years = sorted(merged_data["Aasta"].unique())
selected_year = st.sidebar.selectbox("Vali aasta", years, index=len(years) - 1)

year_data = get_data_for_year(merged_data, selected_year)
total_change = int(year_data["Loomulik iive"].sum())
max_row = year_data.loc[year_data["Loomulik iive"].idxmax()]
min_row = year_data.loc[year_data["Loomulik iive"].idxmin()]

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("Loomulik iive kokku", total_change)
metric_2.metric(
    "Kõrgeim maakond",
    f"{max_row['Maakond']}: {int(max_row['Loomulik iive'])}",
)
metric_3.metric(
    "Madalaim maakond",
    f"{min_row['Maakond']}: {int(min_row['Loomulik iive'])}",
)

table_data = year_data[["Maakond", "Loomulik iive"]].sort_values(
    "Loomulik iive", ascending=False
)

map_col, table_col = st.columns([2, 1])

with map_col:
    st.subheader(f"Kaart aastal {selected_year}")
    fig = plot_map(year_data, selected_year)
    st.pyplot(fig)

with table_col:
    st.subheader(f"Andmed aastal {selected_year}")
    st.dataframe(table_data, use_container_width=True, hide_index=True)
