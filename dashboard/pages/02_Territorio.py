"""Territorio — Mappa regionale e ranking."""

import altair as alt
import pandas as pd
import plotly.express as px
import streamlit as st

from sources import (
    MART_SETTORE,
    YEARS,
    fmt_eur,
    fmt_num,
    fmt_pct,
    load_mart,
    load_mart_years,
)

st.title("🗺️ Territorio")
st.markdown("Distribuzione geografica degli aiuti di Stato per regione.")

# ── Filtri ──────────────────────────────────────────────────────────────────

col_f1, col_f2 = st.columns(2)
with col_f1:
    anno = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="terr_anno")
with col_f2:
    metrica = st.radio(
        "Metrica",
        ["ESL totale", "Media ESL", "N. imprese"],
        horizontal=True,
        key="terr_metrica",
    )

# ── Carica dati ─────────────────────────────────────────────────────────────

df = load_mart("mart_aiuti_per_regione", anno)

metric_col = {
    "ESL totale": "totale_esl",
    "Media ESL": "media_esl",
    "N. imprese": "imprese",
}[metrica]

df_sorted = df.sort_values(metric_col, ascending=False)

# ── Mappa ───────────────────────────────────────────────────────────────────

st.subheader(f"Mappa — {metrica} ({anno})")

# GeoJSON Italia (regioni)
GEOJSON_URL = "https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson"

fig = px.choropleth(
    df,
    geojson=GEOJSON_URL,
    locations="regione_beneficiario",
    featureidkey="properties.reg_name",
    color=metric_col,
    color_continuous_scale="Blues",
    hover_name="regione_beneficiario",
    hover_data={
        "totale_esl": ":,.0f",
        "media_esl": ":,.0f",
        "imprese": ":,.0f",
        "aiuti": ":,.0f",
    },
    labels={
        "totale_esl": "ESL totale",
        "media_esl": "Media ESL",
        "imprese": "Imprese",
        "aiuti": "Aiuti",
    },
)
fig.update_geos(
    fitbounds="locations",
    visible=False,
    bgcolor="rgba(0,0,0,0)",
)
fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    coloraxis_colorbar=dict(title=metrica, ticksuffix="€" if "ESL" in metrica else ""),
    height=500,
    paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig, width='stretch')

st.markdown("---")

# ── Ranking ─────────────────────────────────────────────────────────────────

col_rank, col_detail = st.columns([1, 1])

with col_rank:
    st.subheader(f"📊 Ranking regioni — {metrica}")
    display_df = df_sorted[["regione_beneficiario", metric_col, "imprese", "aiuti"]].copy()
    display_df.columns = ["Regione", metrica, "Imprese", "Aiuti"]
    st.dataframe(
        display_df.reset_index(drop=True),
        width='stretch',
        height=520,
        column_config={
            "Regione": st.column_config.TextColumn("Regione", width="medium"),
            metrica: st.column_config.NumberColumn(metrica, format="%.0f"),
            "Imprese": st.column_config.NumberColumn("Imprese", format="%.0f"),
            "Aiuti": st.column_config.NumberColumn("Aiuti", format="%.0f"),
        },
    )

with col_detail:
    st.subheader("🏭 Settori NACE per regione")

    # Seleziona regione
    regioni_options = sorted(df["regione_beneficiario"].unique())
    sel_regione = st.selectbox("Seleziona regione", regioni_options, key="terr_settore_reg")

    df_sett = load_mart(MART_SETTORE, anno)
    df_sett_r = df_sett[df_sett["regione"] == sel_regione].sort_values("totale_esl", ascending=False)

    if not df_sett_r.empty:
        chart_sett = (
            alt.Chart(df_sett_r.head(10))
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("totale_esl:Q", title="ESL (€)", axis=alt.Axis(format="~s")),
                y=alt.Y("macro_settore:N", title="", sort="-x"),
                tooltip=[
                    alt.Tooltip("macro_settore:N", title="Settore"),
                    alt.Tooltip("totale_esl:Q", title="ESL totale", format=",.0f"),
                    alt.Tooltip("imprese:Q", title="Imprese", format=",.0f"),
                    alt.Tooltip("quota_pct_su_regione:Q", title="% su regione", format=".1f"),
                ],
            )
            .properties(height=320)
        )
        st.altair_chart(chart_sett, width="stretch")
    else:
        st.info("Nessun dato settore disponibile per questa regione.")

# ── Trend regionale ─────────────────────────────────────────────────────────

st.markdown("---")
st.subheader("📈 Trend 5 anni — confronto regioni")

df_all = load_mart_years("mart_aiuti_per_regione")
top_n = st.slider("Top N regioni nel grafico", 3, 20, 5, key="terr_top_n")

top_regions = (
    df_all[df_all["anno"] == anno]
    .nlargest(top_n, "totale_esl")["regione_beneficiario"]
    .tolist()
)
df_trend = df_all[df_all["regione_beneficiario"].isin(top_regions)]

chart_trend = (
    alt.Chart(df_trend)
    .mark_line(point=True, strokeWidth=2)
    .encode(
        x=alt.X("anno:O", title="Anno"),
        y=alt.Y("totale_esl:Q", title="ESL totale (€)", axis=alt.Axis(format="~s")),
        color=alt.Color("regione_beneficiario:N", title="Regione"),
        tooltip=[
            alt.Tooltip("regione_beneficiario:N", title="Regione"),
            alt.Tooltip("anno:O", title="Anno"),
            alt.Tooltip("totale_esl:Q", title="ESL", format=",.0f"),
        ],
    )
    .properties(height=350)
)
st.altair_chart(chart_trend, width="stretch")

st.caption(f"Dati: mart layer su GCS · {anno} · fonte: MIMIT · CC BY 4.0")
