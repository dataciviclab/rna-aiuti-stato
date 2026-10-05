"""Chi eroga — volume vs valore per soggetto concedente."""

import altair as alt
import pandas as pd
import streamlit as st

from sources import (
    MART_CONCEDENTI,
    YEARS,
    fmt_eur,
    fmt_num,
    load_mart,
    load_mart_years,
)

st.title("🏦 Chi eroga")
st.markdown(
    "**Volume vs valore** — chi concede più aiuti per numero di operazioni "
    "e chi per importo. Il Registro non è solo contributi alle PMI: "
    "garanzie, energia e INPS raccontano storie diverse."
)

anno = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="eroga_anno")

df = load_mart(MART_CONCEDENTI, anno)
if df.empty:
    st.warning("Nessun dato disponibile per quest'anno.")
    st.stop()

df_all = load_mart_years(MART_CONCEDENTI)

# ── KPI per tipo ────────────────────────────────────────────────────────────

tipo_agg = (
    df.groupby("tipo_concedente", as_index=False)
    .agg(totale=("totale_esl", "sum"), aiuti=("aiuti", "sum"), imprese=("imprese", "sum"))
    .sort_values("totale", ascending=False)
)

st.subheader(f"Tipologie di concedente — {anno}")
cols = st.columns(min(4, len(tipo_agg)))
for i, row in enumerate(tipo_agg.head(4).itertuples()):
    with cols[i]:
        st.metric(row.tipo_concedente, fmt_eur(row.totale, compact=True), fmt_num(int(row.aiuti)))

st.markdown("---")

# ── Volume vs valore ────────────────────────────────────────────────────────

col_v, col_val = st.columns(2)

with col_v:
    st.subheader("Per numero di aiuti")
    df_vol = df.nlargest(12, "aiuti")
    chart_v = (
        alt.Chart(df_vol)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#3b82f6")
        .encode(
            x=alt.X("aiuti:Q", title="N. aiuti", axis=alt.Axis(format="~s")),
            y=alt.Y("soggetto_concedente:N", title="", sort="-x"),
            color=alt.Color("tipo_concedente:N", title="Tipo"),
            tooltip=[
                alt.Tooltip("soggetto_concedente:N", title="Concedente"),
                alt.Tooltip("tipo_concedente:N", title="Tipo"),
                alt.Tooltip("aiuti:Q", title="Aiuti", format=",.0f"),
                alt.Tooltip("totale_esl:Q", title="ESL", format=",.0f"),
            ],
        )
        .properties(height=420)
    )
    st.altair_chart(chart_v, width="stretch")

with col_val:
    st.subheader("Per importo erogato (ESL)")
    df_val = df.nlargest(12, "totale_esl")
    chart_val = (
        alt.Chart(df_val)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#10b981")
        .encode(
            x=alt.X("totale_esl:Q", title="ESL (€)", axis=alt.Axis(format="~s")),
            y=alt.Y("soggetto_concedente:N", title="", sort="-x"),
            color=alt.Color("tipo_concedente:N", title="Tipo"),
            tooltip=[
                alt.Tooltip("soggetto_concedente:N", title="Concedente"),
                alt.Tooltip("tipo_concedente:N", title="Tipo"),
                alt.Tooltip("totale_esl:Q", title="ESL", format=",.0f"),
                alt.Tooltip("aiuti:Q", title="Aiuti", format=",.0f"),
                alt.Tooltip("imprese:Q", title="Imprese", format=",.0f"),
            ],
        )
        .properties(height=420)
    )
    st.altair_chart(chart_val, width="stretch")

st.markdown("---")

# ── Trend tipologie ─────────────────────────────────────────────────────────

st.subheader("Evoluzione tipologie nel tempo")

df_tipo_all = (
    df_all.groupby(["anno", "tipo_concedente"], as_index=False)
    .agg(totale=("totale_esl", "sum"))
)
top_tipi = (
    df_tipo_all.groupby("tipo_concedente")["totale"]
    .sum()
    .nlargest(6)
    .index.tolist()
)
df_tipo_top = df_tipo_all[df_tipo_all["tipo_concedente"].isin(top_tipi)]

chart_trend = (
    alt.Chart(df_tipo_top)
    .mark_line(point=True, strokeWidth=2)
    .encode(
        x=alt.X("anno:O", title="Anno"),
        y=alt.Y("totale:Q", title="ESL (€)", axis=alt.Axis(format="~s")),
        color=alt.Color("tipo_concedente:N", title="Tipo"),
        tooltip=[
            alt.Tooltip("anno:O", title="Anno"),
            alt.Tooltip("tipo_concedente:N", title="Tipo"),
            alt.Tooltip("totale:Q", title="ESL", format=",.0f"),
        ],
    )
    .properties(height=360)
)
st.altair_chart(chart_trend, width="stretch")

st.markdown("---")

# ── Tabella top ─────────────────────────────────────────────────────────────

st.subheader(f"Top 20 concedenti — {anno}")
display = df.nlargest(20, "totale_esl")[
    ["soggetto_concedente", "tipo_concedente", "aiuti", "totale_esl", "imprese", "quota_pct_su_anno"]
].copy()
display.columns = ["Concedente", "Tipo", "N. aiuti", "ESL", "Imprese", "% anno"]
display["ESL"] = display["ESL"].apply(lambda x: fmt_eur(x, compact=True))
display["N. aiuti"] = display["N. aiuti"].apply(lambda x: fmt_num(int(x)))
display["Imprese"] = display["Imprese"].apply(lambda x: fmt_num(int(x)))
display["% anno"] = display["% anno"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "—")

st.dataframe(
    display.reset_index(drop=True),
    width="stretch",
    height=560,
    column_config={
        "Concedente": st.column_config.TextColumn("Concedente", width="large"),
        "Tipo": st.column_config.TextColumn("Tipo", width="medium"),
        "N. aiuti": st.column_config.TextColumn("N. aiuti", width="small"),
        "ESL": st.column_config.TextColumn("ESL", width="small"),
        "Imprese": st.column_config.TextColumn("Imprese", width="small"),
        "% anno": st.column_config.TextColumn("% anno", width="small"),
    },
)

st.caption(
    "Tipologia classificata per keyword sul soggetto concedente (MCC, SACE, INPS, GSE…). "
    "Le varianti di denominazione dello stesso ente non sono sempre normalizzate."
)
st.caption(f"Dati: mart layer · {anno} · fonte: MIMIT Registro Nazionale Aiuti di Stato · CC BY 4.0")
