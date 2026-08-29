"""Cerca — Ricerca beneficiario nel clean layer."""

import time

import altair as alt
import pandas as pd
import streamlit as st

from sources import YEARS, fmt_eur, run_sql

st.title("🔍 Cerca beneficiario")
st.markdown(
    "Cerca un'azienda per **denominazione** o **codice fiscale**. "
    "La query viene eseguita sul clean layer (tutti gli anni, ~17M righe) "
    "via DuckDB su GCS."
)

# -- Input -------------------------------------------------------------------

col_input, col_years = st.columns([3, 1])
with col_input:
    query_text = st.text_input(
        "Denominazione o codice fiscale",
        placeholder="es. COLDIRETTI, 01234567890...",
        key="cerca_query",
    )
with col_years:
    year_range = st.select_slider(
        "Anni",
        options=YEARS,
        value=(YEARS[0], YEARS[-1]),
        key="cerca_years",
    )

max_rows = st.slider("Righe max", 10, 500, 100, key="cerca_max")

# -- Esecuzione ---------------------------------------------------------------

if query_text:
    years = list(range(year_range[0], year_range[1] + 1))
    q = query_text.strip()
    fields = (
        "denominazione_beneficiario, codice_fiscale_beneficiario, "
        "regione_beneficiario, data_concessione, anno, mese, "
        "soggetto_concedente, titolo_misura, procedimento, "
        "ROUND(elemento_aiuto, 2) AS importo, strumento"
    )

    # Sanitize input SQL — DuckDB è read-only ma previeni injection
    q = query_text.strip().replace("'", "''").replace(";", "").replace("--", "")

    if q.upper().replace(" ", "").isalpha():
        where = f"UPPER(denominazione_beneficiario) LIKE '%{q.upper()}%'"
    else:
        where = f"codice_fiscale_beneficiario LIKE '%{q}%'"

    sql = f"SELECT {fields} FROM clean_input WHERE {where} ORDER BY data_concessione DESC LIMIT {max_rows}"

    with st.spinner(f"Query su {len(years)} anni di dati..."):
        t0 = time.perf_counter()
        try:
            df = run_sql(sql, tuple(years))
            elapsed = time.perf_counter() - t0
        except Exception as e:
            st.error(f"Errore nella query: {e}")
            df = pd.DataFrame()

    if not df.empty:
        k1, k2, k3 = st.columns(3)
        k1.metric("Righe trovate", f"{len(df):,}")
        k2.metric("Tempo", f"{elapsed:.1f}s")
        totale = df["importo"].sum() if "importo" in df.columns else 0
        k3.metric("ESL totale risultati", fmt_eur(totale, compact=True))

        st.markdown("---")
        st.dataframe(
            df,
            width='stretch',
            height=min(400, 40 + len(df) * 35),
            column_config={
                "denominazione_beneficiario": st.column_config.TextColumn("Denominazione", width="large"),
                "codice_fiscale_beneficiario": st.column_config.TextColumn("CF", width="medium"),
                "regione_beneficiario": st.column_config.TextColumn("Regione", width="small"),
                "data_concessione": st.column_config.TextColumn("Data", width="small"),
                "importo": st.column_config.NumberColumn("Importo (EUR)", format="%.2f", width="medium"),
                "procedimento": st.column_config.TextColumn("Procedimento", width="medium"),
            },
        )

        st.markdown("---")
        col_y, col_p = st.columns(2)

        with col_y:
            st.subheader("Breakdown per anno")
            df_by_year = df.groupby("anno", as_index=False).agg(totale=("importo", "sum"), n=("importo", "count"))
            chart_year = (
                alt.Chart(df_by_year)
                .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#3b82f6")
                .encode(
                    x=alt.X("anno:O", title="Anno"),
                    y=alt.Y("totale:Q", title="ESL (EUR)", axis=alt.Axis(format="~s")),
                    tooltip=["anno", alt.Tooltip("totale:Q", format=",.0f"), "n"],
                )
                .properties(height=250)
            )
            st.altair_chart(chart_year, width="stretch")

        with col_p:
            st.subheader("Breakdown per procedimento")
            df_by_proc = df.groupby("procedimento", as_index=False).agg(totale=("importo", "sum")).sort_values("totale", ascending=False)
            chart_proc = (
                alt.Chart(df_by_proc)
                .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#10b981")
                .encode(
                    x=alt.X("totale:Q", title="ESL (EUR)", axis=alt.Axis(format="~s")),
                    y=alt.Y("procedimento:N", title="", sort="-x"),
                    tooltip=["procedimento", alt.Tooltip("totale:Q", format=",.0f")],
                )
                .properties(height=250)
            )
            st.altair_chart(chart_proc, width="stretch")

        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Scarica CSV",
            data=csv_data,
            file_name=f"rna_cerca_{query_text}_{int(time.time())}.csv",
            mime="text/csv",
        )
    else:
        st.info("Nessun risultato trovato.")
else:
    st.info("🔍 Inserisci una denominazione o un codice fiscale per cercare.")

st.caption("Query su DuckDB + parquet clean da GCS. Tempo dipende dagli anni selezionati.")
