"""Cerca — Esplora beneficiari e cerca per nome/CF."""

import time

import altair as alt
import pandas as pd
import streamlit as st

from sources import YEARS, SLUG, fmt_eur, fmt_num, load_mart, run_sql

st.title("🔍 Cerca beneficiario")

# ── Session state per navigazione tra tab ────────────────────────────────────

if "cerca_tab" not in st.session_state:
    st.session_state.cerca_tab = "Top riceventi"
if "cerca_query" not in st.session_state:
    st.session_state.cerca_query = ""

# ── Tab selector (radio orizzontale, controllabile) ──────────────────────────

tab_choice = st.radio(
    "Modalità",
    ["Top riceventi", "Cerca"],
    index=0 if st.session_state.cerca_tab == "Top riceventi" else 1,
    horizontal=True,
    label_visibility="collapsed",
    key="cerca_tab_selector",
)
st.session_state.cerca_tab = tab_choice

# ══════════════════════════════════════════════════════════════════════════════
# TAB: Top riceventi
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.cerca_tab == "Top riceventi":

    st.markdown("Le imprese che hanno ricevuto piu' aiuti di Stato. Clicca su un beneficiario per esplorare nel dettaglio.")

    col_filter, col_chart = st.columns([1, 2])

    with col_filter:
        anno_top = st.selectbox("Anno", YEARS, index=len(YEARS) - 1, key="top_anno")
        n_top = st.slider("Top N", 10, 100, 20, key="top_n")

    with col_chart:
        st.subheader(f"Top {n_top} per importo — {anno_top}")

    df_top = load_mart("mart_aiuti_top_beneficiari", anno_top)

    if df_top.empty:
        st.warning("Nessun dato disponibile per quest'anno.")
    else:
        df_top_n = df_top.sort_values("totale_esl", ascending=False).head(n_top)
        df_top_n = df_top_n.reset_index(drop=True)
        df_top_n.index = df_top_n.index + 1  # indice da 1

        # Tabella cliccabile
        display = df_top_n[[
            "denominazione_beneficiario", "codice_fiscale_beneficiario",
            "regione_beneficiario", "aiuti", "totale_esl",
        ]].copy()
        display.columns = ["Denominazione", "CF", "Regione", "N. aiuti", "ESL totale"]
        display["ESL totale"] = display["ESL totale"].apply(lambda x: fmt_eur(x, compact=True))

        st.dataframe(
            display,
            width="stretch",
            height=min(600, 40 + len(display) * 35),
            column_config={
                "Denominazione": st.column_config.TextColumn("Denominazione", width="large"),
                "CF": st.column_config.TextColumn("CF", width="medium"),
                "Regione": st.column_config.TextColumn("Regione", width="small"),
                "N. aiuti": st.column_config.NumberColumn("N. aiuti", width="small"),
                "ESL totale": st.column_config.TextColumn("ESL totale", width="medium"),
            },
        )

        # Grafico top 15
        if len(df_top_n) >= 5:
            top15 = df_top_n.head(15)
            chart = alt.Chart(top15).mark_bar(
                cornerRadiusTopLeft=3, cornerRadiusTopRight=3, color="#3b82f6"
            ).encode(
                x=alt.X("totale_esl:Q", title="ESL (EUR)", axis=alt.Axis(format="~s")),
                y=alt.Y("denominazione_beneficiario:N", title="", sort="-x"),
                tooltip=[
                    alt.Tooltip("denominazione_beneficiario:N", title="Beneficiario"),
                    alt.Tooltip("totale_esl:Q", title="ESL", format=",.0f"),
                    alt.Tooltip("aiuti:Q", title="N. aiuti"),
                ],
            ).properties(height=max(250, len(top15) * 25))
            st.altair_chart(chart, width="stretch")

        # Bottone per esplorare — popola il tab Cerca
        st.markdown("---")
        st.markdown("**Vuoi esplorare un beneficiario?** Seleziona un CF dalla tabella e clicca il bottone qui sotto.")

        cf_list = df_top_n["codice_fiscale_beneficiario"].tolist()
        nomi_list = df_top_n["denominazione_beneficiario"].tolist()
        options = [f"{cf} — {nomi_list[i][:60]}" for i, cf in enumerate(cf_list)]

        selected = st.selectbox("Beneficiario", options, key="top_select")
        if st.button("🔍 Esplora beneficiario", type="primary", key="top_go"):
            cf_selected = selected.split(" — ")[0].strip()
            st.session_state.cerca_query = cf_selected
            st.session_state.cerca_tab = "Cerca"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB: Cerca (testo libero)
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.cerca_tab == "Cerca":

    col_input, col_years = st.columns([3, 1])
    with col_input:
        query_text = st.text_input(
            "Denominazione o codice fiscale",
            value=st.session_state.cerca_query,
            placeholder="es. COLDIRETTI, 01234567890...",
            key="cerca_query_input",
        )
        # Aggiorna session state se l'utente scrive direttamente
        if query_text and query_text != st.session_state.cerca_query:
            st.session_state.cerca_query = query_text

    with col_years:
        year_range = st.select_slider(
            "Anni",
            options=YEARS,
            value=(YEARS[0], YEARS[-1]),
            key="cerca_years",
        )

    max_rows = st.slider("Righe max", 10, 500, 100, key="cerca_max")

    if query_text:
        years = list(range(year_range[0], year_range[1] + 1))
        q = query_text.strip().replace("'", "''").replace(";", "").replace("--", "")

        if q.upper().replace(" ", "").isalpha():
            where = f"UPPER(denominazione_beneficiario) LIKE '%{q.upper()}%'"
        else:
            where = f"codice_fiscale_beneficiario LIKE '%{q}%'"

        fields = (
            "denominazione_beneficiario, codice_fiscale_beneficiario, "
            "regione_beneficiario, data_concessione, anno, mese, "
            "soggetto_concedente, titolo_misura, procedimento, "
            "ROUND(elemento_aiuto, 2) AS importo, strumento"
        )
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
