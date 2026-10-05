"""Policy & Strumenti — Obiettivi, strumenti e top misure."""

import altair as alt
import pandas as pd
import streamlit as st

from sources import (
    MART_MISURA,
    MART_OBIETTIVO,
    MART_REGIMI,
    MART_STRUMENTO,
    YEARS,
    fmt_eur,
    fmt_num,
    load_mart,
    load_mart_years,
)

st.title("📋 Policy & Strumenti")
st.markdown("Obiettivi delle politiche, strumenti di erogazione e top misure.")

# ── Filtri ──────────────────────────────────────────────────────────────────

anno = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="pol_anno")

# ── Carica dati ─────────────────────────────────────────────────────────────

df_ob = load_mart(MART_OBIETTIVO, anno)
df_str = load_mart(MART_STRUMENTO, anno)

# ── Obiettivi policy ───────────────────────────────────────────────────────

col_ob, col_str = st.columns(2)

with col_ob:
    st.subheader("🎯 Obiettivi policy")
    df_ob_top = df_ob.sort_values("totale_esl", ascending=False).head(10)
    chart_ob = (
        alt.Chart(df_ob_top)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("totale_esl:Q", title="ESL (€)", axis=alt.Axis(format="~s")),
            y=alt.Y("obiettivo:N", title="", sort="-x"),
            tooltip=[
                alt.Tooltip("obiettivo:N", title="Obiettivo"),
                alt.Tooltip("totale_esl:Q", title="ESL totale", format=",.0f"),
                alt.Tooltip("imprese:Q", title="Imprese", format=",.0f"),
                alt.Tooltip("quota_pct_su_anno:Q", title="% annuale", format=".1f"),
            ],
        )
        .properties(height=380)
    )
    st.altair_chart(chart_ob, width="stretch")

with col_str:
    st.subheader("🔧 Strumenti di aiuto")
    df_str_top = df_str.sort_values("totale_esl", ascending=False).head(10)
    chart_str = (
        alt.Chart(df_str_top)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("totale_esl:Q", title="ESL (€)", axis=alt.Axis(format="~s")),
            y=alt.Y("strumento:N", title="", sort="-x"),
            color=alt.Color("strumento:N", legend=None),
            tooltip=[
                alt.Tooltip("strumento:N", title="Strumento"),
                alt.Tooltip("totale_esl:Q", title="ESL totale", format=",.0f"),
                alt.Tooltip("aiuti:Q", title="N. aiuti", format=",.0f"),
                alt.Tooltip("quota_pct_su_anno:Q", title="% annuale", format=".1f"),
            ],
        )
        .properties(height=380)
    )
    st.altair_chart(chart_str, width="stretch")

st.markdown("---")

# ── Evoluzione composizione nel tempo ───────────────────────────────────────

st.subheader("📈 Evoluzione strumenti nel tempo")

df_strum_all = load_mart_years(MART_STRUMENTO)
df_strum_agg = (
    df_strum_all.groupby(["anno", "strumento"], as_index=False)
    .agg(totale=("totale_esl", "sum"))
)

# Solo top 5 strumenti per importo totale
top_strumenti = (
    df_strum_agg.groupby("strumento")["totale"]
    .sum()
    .nlargest(5)
    .index.tolist()
)
df_strum_top = df_strum_agg[df_strum_agg["strumento"].isin(top_strumenti)]

chart_evo = (
    alt.Chart(df_strum_top)
    .mark_area(opacity=0.6)
    .encode(
        x=alt.X("anno:O", title="Anno"),
        y=alt.Y("totale:Q", title="ESL (€)", stack="normalize", axis=alt.Axis(format="%")),
        color=alt.Color("strumento:N", title="Strumento"),
        tooltip=[
            alt.Tooltip("strumento:N", title="Strumento"),
            alt.Tooltip("anno:O", title="Anno"),
            alt.Tooltip("totale:Q", title="ESL", format=",.0f"),
        ],
    )
    .properties(height=350)
)
st.altair_chart(chart_evo, width="stretch")

st.markdown("---")

# ── Regimi UE: cosa autorizza gli aiuti ────────────────────────────────────

st.subheader("🇪🇺 Regimi UE e procedimenti")
st.caption(
    "Il Temporary Crisis Framework e i regimi sulla crisi energetica pesano "
    "oltre metà del valore registrato: non è un dettaglio tecnico."
)

df_reg = load_mart(MART_REGIMI, anno)
df_reg_all = load_mart_years(MART_REGIMI)

if not df_reg.empty:
    col_r1, col_r2 = st.columns(2)

    with col_r1:
        df_reg_top = (
            df_reg.groupby("regime", as_index=False)
            .agg(totale=("totale_esl", "sum"), aiuti=("aiuti", "sum"))
            .sort_values("totale", ascending=False)
            .head(8)
        )
        chart_reg = (
            alt.Chart(df_reg_top)
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
            .encode(
                x=alt.X("totale:Q", title="ESL (€)", axis=alt.Axis(format="~s")),
                y=alt.Y("regime:N", title="", sort="-x"),
                tooltip=[
                    alt.Tooltip("regime:N", title="Regime"),
                    alt.Tooltip("totale:Q", title="ESL", format=",.0f"),
                    alt.Tooltip("aiuti:Q", title="N. aiuti", format=",.0f"),
                ],
            )
            .properties(height=340)
        )
        st.altair_chart(chart_reg, width="stretch")

    with col_r2:
        df_proc_reg = (
            df_reg.groupby("procedimento", as_index=False)
            .agg(totale=("totale_esl", "sum"))
            .sort_values("totale", ascending=False)
        )
        chart_proc_reg = (
            alt.Chart(df_proc_reg)
            .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#6366f1")
            .encode(
                x=alt.X("totale:Q", title="ESL (€)", axis=alt.Axis(format="~s")),
                y=alt.Y("procedimento:N", title="", sort="-x"),
                tooltip=["procedimento", alt.Tooltip("totale:Q", format=",.0f")],
            )
            .properties(height=340)
        )
        st.altair_chart(chart_proc_reg, width="stretch")

    if not df_reg_all.empty:
        st.subheader("Evoluzione regimi UE nel tempo")
        df_reg_trend = (
            df_reg_all.groupby(["anno", "regime"], as_index=False)
            .agg(totale=("totale_esl", "sum"))
        )
        top_reg = (
            df_reg_trend.groupby("regime")["totale"]
            .sum()
            .nlargest(6)
            .index.tolist()
        )
        df_reg_trend_top = df_reg_trend[df_reg_trend["regime"].isin(top_reg)]
        chart_reg_trend = (
            alt.Chart(df_reg_trend_top)
            .mark_line(point=True, strokeWidth=2)
            .encode(
                x=alt.X("anno:O", title="Anno"),
                y=alt.Y("totale:Q", title="ESL (€)", axis=alt.Axis(format="~s")),
                color=alt.Color("regime:N", title="Regime"),
                tooltip=["anno", "regime", alt.Tooltip("totale:Q", format=",.0f")],
            )
            .properties(height=340)
        )
        st.altair_chart(chart_reg_trend, width="stretch")
else:
    st.info("Mart regimi non disponibile per l'anno selezionato.")

st.markdown("---")

# ── Top misure per EROGATO effettivo (join aiuti × misure) ─────────────────

st.subheader("📜 Top 20 misure per importo erogato")
st.caption("Quanto è stato **effettivamente concesso** agli aiuti collegati a ogni misura (join su `car` con RNA Misure). Il plafond è la capacità autorizzata della misura.")

df_misure = load_mart(MART_MISURA, anno)
df_misure_sorted = df_misure.sort_values("totale_esl", ascending=False).head(20)

display_misure = df_misure_sorted[[
    "titolo_misura", "des_tipo_misura", "imprese", "aiuti", "totale_esl", "plafond_totale",
]].copy()
display_misure.columns = ["Misura", "Tipo", "Imprese", "N. aiuti", "Erogato", "Plafond"]
for c in ("Erogato", "Plafond"):
    display_misure[c] = display_misure[c].apply(lambda x: fmt_eur(x, compact=True) if pd.notna(x) else "—")
display_misure["Imprese"] = display_misure["Imprese"].apply(lambda x: fmt_num(x) if pd.notna(x) else "—")
display_misure["N. aiuti"] = display_misure["N. aiuti"].apply(lambda x: fmt_num(x) if pd.notna(x) else "—")

st.dataframe(
    display_misure.reset_index(drop=True),
    width='stretch',
    height=560,
    column_config={
        "Misura": st.column_config.TextColumn("Misura", width="large"),
        "Tipo": st.column_config.TextColumn("Tipo", width="medium"),
        "Imprese": st.column_config.TextColumn("Imprese", width="small"),
        "N. aiuti": st.column_config.TextColumn("N. aiuti", width="small"),
        "Erogato": st.column_config.TextColumn("Erogato", width="small"),
        "Plafond": st.column_config.TextColumn("Plafond", width="small"),
    },
)

st.caption(f"Dati: mart layer su GCS · {anno} · fonte: MIMIT · CC BY 4.0")
