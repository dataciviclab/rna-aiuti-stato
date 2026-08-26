"""Policy & Strumenti — Obiettivi, strumenti e top misure."""

import altair as alt
import pandas as pd
import streamlit as st

from sources import (
    MART_OBIETTIVO,
    MART_STRUMENTO,
    YEARS,
    SLUG_MISURE,
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

# ── Top misure (da rna_misure) ─────────────────────────────────────────────

st.subheader("📜 Top 20 misure per importo garantito")

df_misure = load_mart("mart_top_misure", 2023, SLUG_MISURE)
df_misure_sorted = df_misure.sort_values("totale_eur", ascending=False).head(20)

display_misure = df_misure_sorted[[
    "titolo_misura", "des_tipo_misura", "totale_eur",
]].copy()
display_misure.columns = ["Misure", "Tipo", "Totale EUR"]
display_misure["Totale EUR"] = display_misure["Totale EUR"].apply(lambda x: fmt_eur(x) if pd.notna(x) else "—")

st.dataframe(
    display_misure.reset_index(drop=True),
    use_container_width=True,
    height=560,
    column_config={
        "Misure": st.column_config.TextColumn("Misure", width="large"),
        "Tipo": st.column_config.TextColumn("Tipo", width="medium"),
        "Totale EUR": st.column_config.TextColumn("Totale EUR", width="medium"),
    },
)

st.caption(f"Dati: mart layer su GCS · {anno} · fonte: MIMIT · CC BY 4.0")
