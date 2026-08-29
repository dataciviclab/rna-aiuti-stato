"""Panoramica — KPI, trend annuale, composizione aiuti."""

import altair as alt
import pandas as pd
import streamlit as st

from sources import (
    MART_OBIETTIVO,
    MART_PROCEDIMENTO,
    MART_REGIONE,
    MART_STRUMENTO,
    MART_TIPO_BENEF,
    YEARS,
    SLUG,
    fmt_eur,
    fmt_num,
    load_mart,
    load_mart_years,
    run_sql,
)

st.title("🇮🇹 RNA Aiuti di Stato")
st.markdown("**Panoramica** — Il quadro nazionale degli aiuti pubblici alle imprese italiane.")

# ── Filtri ──────────────────────────────────────────────────────────────────

col_filter1, col_filter2 = st.columns(2)
with col_filter1:
    anno = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="overview_anno")
with col_filter2:
    regione = st.selectbox(
        "Regione (opzionale)",
        ["Tutte"] + sorted([
            "Abruzzo", "Basilicata", "Calabria", "Campania", "Emilia-Romagna",
            "Friuli Venezia Giulia", "Lazio", "Liguria", "Lombardia", "Marche",
            "Molise", "Piemonte", "Puglia", "Sardegna", "Sicilia",
            "Toscana", "Trentino-Alto Adige", "Umbria", "Valle d'Aosta", "Veneto",
        ]),
        index=0,
        key="overview_regione",
    )

# ── Carica dati ─────────────────────────────────────────────────────────────

df_reg = load_mart(MART_REGIONE, anno)
df_proc = load_mart(MART_PROCEDIMENTO, anno)
df_tipo = load_mart(MART_TIPO_BENEF, anno)
df_strum = load_mart(MART_STRUMENTO, anno)

if regione != "Tutte":
    df_reg_r = df_reg[df_reg["regione_beneficiario"] == regione]
    df_tipo_r = df_tipo[df_tipo["regione_beneficiario"] == regione]
else:
    df_reg_r = df_reg
    df_tipo_r = df_tipo

# ── KPI ────────────────────────────────────────────────────────────────────

totale_esl = df_reg_r["totale_esl"].sum()
n_aiuti = df_reg_r["aiuti"].sum()
n_imprese = df_reg_r["imprese"].sum()
n_regioni = df_reg_r["regione_beneficiario"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("ESL totale", fmt_eur(totale_esl, compact=True))
k2.metric("N. aiuti", fmt_num(int(n_aiuti)))
k3.metric("N. imprese", fmt_num(int(n_imprese)))
k4.metric("Regioni", n_regioni)

st.markdown("---")

# ── Trend annuale ───────────────────────────────────────────────────────────

st.subheader("📈 Trend annuale ESL totale")

df_trend = load_mart_years(MART_REGIONE)
df_trend_agg = (
    df_trend.groupby("anno", as_index=False)
    .agg(totale_esl=("totale_esl", "sum"), n_imprese=("imprese", "sum"))
)

chart_trend = (
    alt.Chart(df_trend_agg)
    .mark_line(point=True, color="#3b82f6", strokeWidth=2.5)
    .encode(
        x=alt.X("anno:O", title="Anno"),
        y=alt.Y("totale_esl:Q", title="ESL totale (€)", axis=alt.Axis(format="~s")),
        tooltip=[
            alt.Tooltip("anno:O", title="Anno"),
            alt.Tooltip("totale_esl:Q", title="ESL totale", format=",.0f"),
            alt.Tooltip("n_imprese:Q", title="Imprese", format=",.0f"),
        ],
    )
    .properties(height=300)
)
st.altair_chart(chart_trend, width="stretch")

st.markdown("---")

# ── De Minimis vs Notifica ─────────────────────────────────────────────────

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("⚖️ Procedimento")
    df_proc_agg = (
        df_proc.groupby("procedimento", as_index=False)
        .agg(totale=("totale_esl", "sum"))
        .sort_values("totale", ascending=False)
    )
    chart_proc = (
        alt.Chart(df_proc_agg)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("totale:Q", title="ESL (€)", axis=alt.Axis(format="~s")),
            y=alt.Y("procedimento:N", title="", sort="-x"),
            color=alt.Color("procedimento:N", legend=None),
            tooltip=[
                alt.Tooltip("procedimento:N", title="Procedimento"),
                alt.Tooltip("totale:Q", title="ESL totale", format=",.0f"),
            ],
        )
        .properties(height=200)
    )
    st.altair_chart(chart_proc, width="stretch")

with col_right:
    st.subheader("🏢 Tipo beneficiario")
    df_tipo_agg = (
        df_tipo_r.groupby("tipo_beneficiario", as_index=False)
        .agg(totale=("totale_esl", "sum"))
        .sort_values("totale", ascending=False)
    )
    chart_tipo = (
        alt.Chart(df_tipo_agg)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("totale:Q", title="ESL (€)", axis=alt.Axis(format="~s")),
            y=alt.Y("tipo_beneficiario:N", title="", sort="-x"),
            color=alt.Color("tipo_beneficiario:N", legend=None),
            tooltip=[
                alt.Tooltip("tipo_beneficiario:N", title="Tipo"),
                alt.Tooltip("totale:Q", title="ESL totale", format=",.0f"),
            ],
        )
        .properties(height=200)
    )
    st.altair_chart(chart_tipo, width="stretch")

st.markdown("---")

# ── Strumenti ───────────────────────────────────────────────────────────────

st.subheader("🔧 Strumenti di aiuto")
df_strum_agg = (
    df_strum.groupby("strumento", as_index=False)
    .agg(totale=("totale_esl", "sum"), n=("aiuti", "sum"))
    .sort_values("totale", ascending=False)
    .head(8)
)
chart_strum = (
    alt.Chart(df_strum_agg)
    .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
    .encode(
        x=alt.X("totale:Q", title="ESL (€)", axis=alt.Axis(format="~s")),
        y=alt.Y("strumento:N", title="", sort="-x"),
        tooltip=[
            alt.Tooltip("strumento:N", title="Strumento"),
            alt.Tooltip("totale:Q", title="ESL totale", format=",.0f"),
            alt.Tooltip("n:Q", title="N. aiuti", format=",.0f"),
        ],
    )
    .properties(height=280)
)
st.altair_chart(chart_strum, width="stretch")

# ── Fonte ───────────────────────────────────────────────────────────────────

st.caption(
    f"Dati: clean layer {SLUG} su GCS · {anno} · "
    f"fonte: MIMIT Registro Nazionale Aiuti di Stato · CC BY 4.0"
)
