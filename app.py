import streamlit as st
import pandas as pd
import requests
import time
import math
import base64
from sqm_analyzer import (
    DEFAULT_ORIGIN,
    CURATED_SITES,
    generate_lpm_token,
    query_lpm_point,
    query_driving_route,
    calculate_routes_for_origin,
    evaluate_all_sites,
    search_locations
)

st.set_page_config(
    page_title="SQM & Driving Time Explorer",
    page_icon="🌌",
    layout="wide"
)

st.title("🌌 Ricerca Siti Astronomici Bui (SQM & Tempi Auto)")
st.markdown(
    """
    Questo strumento supera il limite della ricerca "in linea d'aria" di *LightPollutionMap*,
    valutando l'**effettiva raggiungibilità in auto** (tempi di percorrenza e distanze reali su strada)
    e i valori fotometrici **SQM / Bortle** aggiornati dai server di *LightPollutionMap.info*.  
    Copertura estesa: **Triveneto** (Friuli-Venezia Giulia, Veneto, Trentino-Alto Adige), **Carinzia (Austria)**, **Slovenia Occidentale** e **Costa & Lagune**.
    """
)

# 1. Inizializza session_state per il punto di partenza: Ghirano predefinito lanciato subito
if "origin_name" not in st.session_state:
    st.session_state.origin_name = DEFAULT_ORIGIN["name"]
if "origin_lat" not in st.session_state:
    st.session_state.origin_lat = DEFAULT_ORIGIN["lat"]
if "origin_lon" not in st.session_state:
    st.session_state.origin_lon = DEFAULT_ORIGIN["lon"]

# Inizializza session_state per il punto personalizzato di test
if "test_lat" not in st.session_state:
    st.session_state.test_lat = 46.4795
if "test_lon" not in st.session_state:
    st.session_state.test_lon = 12.5855
if "test_name" not in st.session_state:
    st.session_state.test_name = "Casera Razzo"

# ----------------- SIDEBAR -----------------
st.sidebar.header("📍 Punto di Partenza")

# Barra di ricerca automatica della località di partenza
search_query = st.sidebar.text_input(
    "🔍 Cerca Città o Comune di partenza",
    placeholder="Es. Ghirano, Pordenone, Treviso, Udine...",
    key="origin_search_input"
)

if search_query:
    with st.sidebar:
        with st.spinner("Ricerca in corso..."):
            found = search_locations(search_query)
            if found:
                options = {f"📍 {p['name']}": p for p in found}
                selected_label = st.selectbox(
                    "Seleziona tra i risultati:",
                    options=list(options.keys()),
                    key="origin_select_box"
                )
                if st.button("✅ Imposta questa partenza", width="stretch"):
                    chosen = options[selected_label]
                    st.session_state.origin_name = chosen["name"]
                    st.session_state.origin_lat = chosen["lat"]
                    st.session_state.origin_lon = chosen["lon"]
                    st.rerun()
            else:
                st.caption("⚠️ Nessuna località trovata. Prova a specificare il comune o la provincia.")

st.sidebar.markdown(f"**Partenza attiva:**  \n📍 `{st.session_state.origin_name}`")
st.sidebar.caption(f"Coordinate: `{st.session_state.origin_lat:.4f}, {st.session_state.origin_lon:.4f}`")

# Pulsante di ripristino rapido a Ghirano se diverso
if st.session_state.origin_name != DEFAULT_ORIGIN["name"]:
    if st.sidebar.button("🔄 Ripristina Ghirano di Prata", width="stretch"):
        st.session_state.origin_name = DEFAULT_ORIGIN["name"]
        st.session_state.origin_lat = DEFAULT_ORIGIN["lat"]
        st.session_state.origin_lon = DEFAULT_ORIGIN["lon"]
        st.rerun()

with st.sidebar.expander("🛠️ Modifica coordinate a mano"):
    manual_name = st.text_input("Nome", value=st.session_state.origin_name)
    manual_lat = st.number_input("Latitudine", value=st.session_state.origin_lat, format="%.5f")
    manual_lon = st.number_input("Longitudine", value=st.session_state.origin_lon, format="%.5f")
    if manual_name != st.session_state.origin_name or manual_lat != st.session_state.origin_lat or manual_lon != st.session_state.origin_lon:
        if st.button("Salva coordinate manuali"):
            st.session_state.origin_name = manual_name
            st.session_state.origin_lat = manual_lat
            st.session_state.origin_lon = manual_lon
            st.rerun()

# ----------------- CARICAMENTO DATI SITI (ISTANTANEO) -----------------
@st.cache_data(ttl=3600)
def get_sites_data(lat, lon, origin_label):
    return calculate_routes_for_origin(lat, lon, origin_label)

sites_data = get_sites_data(st.session_state.origin_lat, st.session_state.origin_lon, st.session_state.origin_name)

# ----------------- TABS -----------------
tab_ranking, tab_test_point, tab_map_view = st.tabs(["🏆 Classifica Siti Bui", "🔍 Testa un Punto Personalizzato", "🗺️ Mappa Interattiva"])

with tab_ranking:
    st.subheader(f"📍 Tutti i Siti di Osservazione Ordinati per Tempo di Guida da {st.session_state.origin_name}")
    st.write(f"Trovati **{len(sites_data)}** siti montani e costieri pronti per l'osservazione, ordinati dal più vicino al più lontano.")
    
    table_rows = []
    for idx, s in enumerate(sites_data, 1):
        table_rows.append({
            "#": idx,
            "Località": s["name"],
            "Area": s.get("macro_region", "Altro"),
            "Zona": s["region"],
            "SQM 2025": s.get("sqm_2025", 0.0),
            "Quota (m)": int(s.get("elevation_m", 0)),
            "Tempo Auto": s.get("duration_str", "N/D"),
            "Distanza (km)": s.get("distance_km", 0.0),
            "Bortle": s.get("bortle", "N/D"),
            "Google Maps": s.get("gmaps_url", "")
        })
        
    df = pd.DataFrame(table_rows)
    if not df.empty:
        def style_rows_by_sqm(row):
            sqm = row["SQM 2025"]
            if sqm >= 21.75:
                # Verde scuro (SQM >= 21.75) con testo nero ad alto contrasto
                style = "background-color: #86efac; color: #000000; font-weight: 600;"
            elif sqm >= 21.70:
                # Verde smeraldo (SQM 21.70 - 21.74)
                style = "background-color: #bbf7d0; color: #000000; font-weight: 600;"
            elif sqm >= 21.50:
                # Blu pastello (SQM 21.50 - 21.69)
                style = "background-color: #bfdbfe; color: #000000; font-weight: 600;"
            elif sqm >= 21.00:
                # Viola pastello (SQM 21.00 - 21.49)
                style = "background-color: #ddd6fe; color: #000000; font-weight: 600;"
            else:
                # Giallo / Ambra pastello (SQM 20.00 - 20.99)
                style = "background-color: #fef08a; color: #000000; font-weight: 600;"
            return [style] * len(row)

        display_cols = ["#", "Località", "Area", "Zona", "SQM 2025", "Quota (m)", "Tempo Auto", "Distanza (km)", "Bortle"]
        styled_df = df[display_cols].style.apply(style_rows_by_sqm, axis=1).format({
            "SQM 2025": "{:.2f}",
            "Quota (m)": "{:d}",
            "Distanza (km)": "{:.1f}"
        })

        st.dataframe(
            styled_df,
            width="stretch",
            hide_index=True
        )
        
        st.markdown("### 📋 Dettagli dei Siti e Accessibilità Auto")
        for idx, s in enumerate(sites_data, 1):
            with st.expander(f"#{idx} - {s['name']}  |  {s.get('macro_region', '')}  |  SQM: {s.get('sqm_2025')}  |  🚗 {s.get('duration_str')} ({s.get('distance_km')} km)  |  🏔️ {int(s.get('elevation_m', 0))}m"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Area:** {s.get('macro_region', '')} • **Dettaglio Zona:** {s['region']}")
                    st.write(f"**Caratteristiche e Accesso:** {s['access']}")
                    st.write(f"**Classe Bortle:** {s.get('bortle')} • **NELM:** {s.get('nelm')} mag")
                    st.write(f"**Coordinate:** `{s['lat']:.4f}, {s['lon']:.4f}`")
                with col2:
                    st.link_button("🧭 Naviga con Google Maps", s.get("gmaps_url", ""), width="stretch")

with tab_test_point:
    st.subheader("🔍 Testa un Punto Qualsiasi (Città, Valico o Coordinate GPS)")
    st.write("Puoi cercare una località per nome oppure inserire manualmente le coordinate geografiche:")
    
    test_search = st.text_input(
        "🔎 Cerca località di destinazione per nome",
        placeholder="Es. Passo Giau, Sauris, Piancavallo, Mangart, Emberger Alm...",
        key="test_search_input"
    )
    if test_search:
        with st.spinner("Ricerca località in corso..."):
            test_found = search_locations(test_search)
            if test_found:
                test_opts = {f"📍 {p['name']}": p for p in test_found}
                selected_test = st.selectbox("Seleziona tra i risultati:", options=list(test_opts.keys()))
                if st.button("📥 Usa queste coordinate per il test"):
                    c_test = test_opts[selected_test]
                    st.session_state.test_name = c_test["name"]
                    st.session_state.test_lat = c_test["lat"]
                    st.session_state.test_lon = c_test["lon"]
                    st.rerun()
            else:
                st.caption("Nessuna destinazione trovata con questo nome. Prova a inserire le coordinate sotto.")

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.test_lat = st.number_input("Latitudine destinazione", value=st.session_state.test_lat, format="%.5f")
    with c2:
        st.session_state.test_lon = st.number_input("Longitudine destinazione", value=st.session_state.test_lon, format="%.5f")
        
    if st.button("🚀 Interroga LightPollutionMap & Calcola Itinerario"):
        with st.spinner(f"Interrogazione raster LPM e calcolo percorso OSRM da {st.session_state.origin_name}..."):
            res_lpm = query_lpm_point(st.session_state.test_lat, st.session_state.test_lon)
            res_route = query_driving_route(st.session_state.origin_lat, st.session_state.origin_lon, st.session_state.test_lat, st.session_state.test_lon)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("SQM 2025", f"{res_lpm['sqm_2025']} mag/arcsec²")
            m2.metric("Tempo di Guida", res_route["duration_str"])
            m3.metric("Distanza Stradale", f"{res_route['distance_km']} km")
            m4.metric("Quota Terreno", f"{res_lpm['elevation_m']} m")
            
            st.info(f"**Località:** {st.session_state.test_name} • **Bortle:** {res_lpm['bortle']} • **NELM:** {res_lpm['nelm']} mag")
            gmaps = f"https://www.google.com/maps/dir/?api=1&origin={st.session_state.origin_lat},{st.session_state.origin_lon}&destination={st.session_state.test_lat},{st.session_state.test_lon}&travelmode=driving"
            st.link_button("🧭 Apri Itinerario in Google Maps", gmaps)

with tab_map_view:
    st.subheader("🗺️ Mappa Interattiva dei Siti")
    st.info("💡 **Clicca sulla mappa:** Clicca in **qualsiasi punto** per calcolare all'istante l'SQM e tracciare l'itinerario in auto con tempi e distanze da " + st.session_state.origin_name + "!")
    st.write("La mappa include tutte le località montane e costiere di Triveneto, Carinzia e Slovenia Occidentale.")
    try:
        with open("sqm_dark_sites_map.html", "r", encoding="utf-8") as f:
            map_html = f.read()
        if hasattr(st, "iframe"):
            st.iframe(map_html, height=720, width="stretch")
        else:
            st.components.v1.html(map_html, height=720, scrolling=True)
    except Exception as e:
        st.error(f"Impossibile caricare la mappa: {e}")
