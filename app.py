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
    evaluate_all_sites
)

st.set_page_config(
    page_title="SQM & Driving Time Explorer",
    page_icon="🌌",
    layout="wide"
)

st.title("🌌 Ricerca Siti Astronomici Buoi (SQM & Tempi Auto)")
st.markdown(
    """
    Questo strumento supera il limite della ricerca "in linea d'aria" di *LightPollutionMap*,
    valutando l'**effettiva raggiungibilità in auto** (tempi di percorrenza e distanze reali su strada)
    e i valori fotometrici **SQM / Bortle** dai server di *LightPollutionMap.info*.
    """
)

# Sidebar: Parametri di ricerca
st.sidebar.header("⚙️ Impostazioni di Partenza")
origin_name = st.sidebar.text_input("Punto di partenza", value=DEFAULT_ORIGIN["name"])
origin_lat = st.sidebar.number_input("Latitudine partenza", value=DEFAULT_ORIGIN["lat"], format="%.4f")
origin_lon = st.sidebar.number_input("Longitudine partenza", value=DEFAULT_ORIGIN["lon"], format="%.4f")
current_origin = {"name": origin_name, "lat": origin_lat, "lon": origin_lon}

st.sidebar.header("🎯 Filtri Siti")
min_sqm = st.sidebar.slider("Soglia Minima SQM (mag/arcsec²)", min_value=21.0, max_value=22.0, value=21.5, step=0.05)
max_drive_hours = st.sidebar.slider("Tempo Max Guida (ore)", min_value=1.0, max_value=3.5, value=2.5, step=0.25)
only_paved = st.sidebar.checkbox("Solo strade completamente asfaltate", value=True)

# Tabs
tab_ranking, tab_test_point, tab_map_view = st.tabs(["🏆 Classifica Siti Buoi", "🔍 Testa un Punto Personalizzato", "🗺️ Mappa Interattiva"])

@st.cache_data(ttl=3600)
def get_sites_data(lat, lon):
    return evaluate_all_sites(origin={"name": origin_name, "lat": lat, "lon": lon}, min_sqm=20.5)

sites_data = get_sites_data(origin_lat, origin_lon)

# Filtra
filtered = [
    s for s in sites_data
    if (s["sqm_2025"] or 0) >= min_sqm
    and (s["duration_min"] / 60.0) <= max_drive_hours
    and (not only_paved or s.get("paved", True))
]

with tab_ranking:
    st.subheader(f"📍 Siti con SQM ≥ {min_sqm:.2f} entro {max_drive_hours}h da {origin_name}")
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
    st.subheader("🔍 Testa un Punto Qualsiasi (Coordinate GPS)")
    st.write("Inserisci le coordinate di un punto montano qualsiasi per calcolarne SQM e tempo di guida reale da Ghirano:")
    
    c1, c2 = st.columns(2)
    with c1:
        test_lat = st.number_input("Latitudine", value=46.4795, format="%.5f")
    with c2:
        test_lon = st.number_input("Longitudine", value=12.5855, format="%.5f")
        
    if st.button("🚀 Interroga LightPollutionMap & Calcola Itinerario"):
        with st.spinner("Interrogazione raster LPM e calcolo percorso OSRM..."):
            res_lpm = query_lpm_point(test_lat, test_lon)
            res_route = query_driving_route(origin_lat, origin_lon, test_lat, test_lon)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("SQM 2025", f"{res_lpm['sqm_2025']} mag/arcsec²")
            m2.metric("Tempo di Guida", res_route["duration_str"])
            m3.metric("Distanza Stradale", f"{res_route['distance_km']} km")
            m4.metric("Quota Terreno", f"{res_lpm['elevation_m']} m")
            
            st.info(f"**Bortle:** {res_lpm['bortle']} • **NELM:** {res_lpm['nelm']} mag")
            gmaps = f"https://www.google.com/maps/dir/?api=1&origin={origin_lat},{origin_lon}&destination={test_lat},{test_lon}&travelmode=driving"
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
