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
    e i valori fotometrici **SQM / Bortle** dai server di *LightPollutionMap.info*.
    """
)

# Inizializza session_state per il punto di partenza
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
    placeholder="Es. Ghirano, Pordenone, Treviso...",
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

st.sidebar.header("🎯 Filtri Siti")
min_sqm = st.sidebar.slider("Soglia Minima SQM (mag/arcsec²)", min_value=19.5, max_value=22.0, value=20.5, step=0.05)
max_drive_hours = st.sidebar.slider("Tempo Max Guida (ore)", min_value=1.0, max_value=3.5, value=2.5, step=0.25)
only_paved = st.sidebar.checkbox("Solo strade completamente asfaltate", value=True)

# ----------------- TABS -----------------
tab_ranking, tab_test_point, tab_map_view = st.tabs(["🏆 Classifica Siti Bui", "🔍 Testa un Punto Personalizzato", "🗺️ Mappa Interattiva"])

@st.cache_data(ttl=3600)
def get_sites_data(lat, lon, origin_label):
    return evaluate_all_sites(origin={"name": origin_label, "lat": lat, "lon": lon}, min_sqm=19.5)

sites_data = get_sites_data(st.session_state.origin_lat, st.session_state.origin_lon, st.session_state.origin_name)

# Filtra
filtered = [
    s for s in sites_data
    if (s["sqm_2025"] or 0) >= min_sqm
    and (s["duration_min"] / 60.0) <= max_drive_hours
    and (not only_paved or s.get("paved", True))
]

with tab_ranking:
    st.subheader(f"📍 Siti con SQM ≥ {min_sqm:.2f} entro {max_drive_hours}h da {st.session_state.origin_name}")
    st.write(f"Trovati **{len(filtered)}** siti idonei ordinati per tempo reale di guida.")
    
    table_rows = []
    for idx, s in enumerate(filtered, 1):
        table_rows.append({
            "#": idx,
            "Località": s["name"],
            "Zona": s["region"],
            "SQM 2025": s["sqm_2025"],
            "SQM 2015": s["sqm_2015"],
            "Quota (m)": int(s["elevation_m"]),
            "Tempo Auto": s["duration_str"],
            "Distanza (km)": s["distance_km"],
            "Bortle": s["bortle"],
            "Google Maps": s["gmaps_url"]
        })
        
    df = pd.DataFrame(table_rows)
    if not df.empty:
        st.dataframe(
            df[["#", "Località", "Zona", "SQM 2025", "Quota (m)", "Tempo Auto", "Distanza (km)", "Bortle"]],
            width="stretch",
            hide_index=True
        )
        
        st.markdown("### 📋 Dettagli dei Siti e Accessibilità Auto")
        for idx, s in enumerate(filtered, 1):
            with st.expander(f"#{idx} - {s['name']}  |  SQM: {s['sqm_2025']}  |  🚗 {s['duration_str']} ({s['distance_km']} km)  |  🏔️ {int(s['elevation_m'])}m"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Regione / Valico:** {s['region']}")
                    st.write(f"**Caratteristiche e Accesso:** {s['access']}")
                    st.write(f"**Classe Bortle:** {s['bortle']} • **NELM (Mag. limite occhio nudo):** {s['nelm']}")
                    st.write(f"**Coordinate:** `{s['lat']:.4f}, {s['lon']:.4f}`")
                with col2:
                    st.link_button("🧭 Naviga con Google Maps", s["gmaps_url"], width="stretch")
    else:
        st.warning("Nessun sito trovato con i filtri attuali. Prova ad abbassare la soglia SQM o aumentare il tempo di guida.")

with tab_test_point:
    st.subheader("🔍 Testa un Punto Qualsiasi (Città, Valico o Coordinate GPS)")
    st.write("Puoi cercare una località per nome oppure inserire manualmente le coordinate geografiche:")
    
    # Ricerca rapida del punto da testare
    test_search = st.text_input(
        "🔎 Cerca località di destinazione per nome",
        placeholder="Es. Passo Giau, Sauris, Piancavallo, Cortina d'Ampezzo...",
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
    st.write("La mappa completa con tracciati OSRM è disponibile anche aprendo direttamente il file `sqm_dark_sites_map.html` nel browser.")
    try:
        with open("sqm_dark_sites_map.html", "r", encoding="utf-8") as f:
            map_html = f.read()
        if hasattr(st, "iframe"):
            st.iframe(map_html, height=700, width="stretch")
        else:
            st.components.v1.html(map_html, height=700, scrolling=True)
    except Exception as e:
        st.error(f"Impossibile caricare la mappa: {e}")
