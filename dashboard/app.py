#!/usr/bin/env python3
"""
RNA Aiuti di Stato · Dashboard Streamlit
17 milioni di aiuti pubblici alle imprese italiane, 2017–2026.
"""

import streamlit as st

st.set_page_config(
    page_title="RNA Aiuti di Stato · Dashboard",
    page_icon="🇮🇹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Navigazione
pages = {
    "": [
        st.Page("pages/01_Overview.py", title="Panoramica", icon="📊", default=True),
    ],
    "Analisi": [
        st.Page("pages/02_Territorio.py", title="Territorio", icon="🗺️"),
        st.Page("pages/03_Policy.py", title="Policy & Strumenti", icon="📋"),
    ],
    "Esplora": [
        st.Page("pages/04_Cerca.py", title="Cerca beneficiario", icon="🔍"),
        st.Page("pages/05_SQL.py", title="Query SQL", icon="🧪"),
    ],
}

pg = st.navigation(pages, position="sidebar")

st.sidebar.markdown("---")
st.sidebar.caption("Dati: [Registro Nazionale Aiuti di Stato](https://www.registroNazionaleTrasparenza.it/) · MIMIT")
st.sidebar.caption("Codice: [dataciviclab/rna-aiuti-stato](https://github.com/dataciviclab/rna-aiuti-stato)")
st.sidebar.caption("[DataCivicLab](https://dataciviclab.org/) · CC BY 4.0")

pg.run()
