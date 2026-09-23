import streamlit as st
import pandas as pd
import requests
import time
import math
import os
import base64
from sqm_analyzer import (
    DEFAULT_ORIGIN,
    CURATED_SITES,
    PROFILES,
    get_profile,
    list_profiles,
    generate_lpm_token,
    query_lpm_point,
    query_driving_route,
    calculate_routes_for_origin,
    evaluate_all_sites,
    search_locations,
    list_available_catalogs,
    load_catalog,
    generate_interactive_html
)

st.set_page_config(
    page_title="SQM & Driving Time Explorer",
    page_icon="🌌",
    layout="wide"
)

# 1. Inizializza session_state per il profilo territoriale (Triveneto predefinito all'avvio)
if "active_profile" not in st.session_state:
    st.session_state.active_profile = "triveneto"

active_prof = get_profile(st.session_state.active_profile)

if "origin_name" not in st.session_state:
    st.session_state.origin_name = active_prof["default_origin"]["name"]
if "origin_lat" not in st.session_state:
    st.session_state.origin_lat = active_prof["default_origin"]["lat"]
if "origin_lon" not in st.session_state:
    st.session_state.origin_lon = active_prof["default_origin"]["lon"]

# Inizializza session_state per il punto personalizzato di test
if "test_lat" not in st.session_state:
    st.session_state.test_lat = active_prof["default_test"]["lat"]
if "test_lon" not in st.session_state:
    st.session_state.test_lon = active_prof["default_test"]["lon"]
if "test_name" not in st.session_state:
    st.session_state.test_name = active_prof["default_test"]["name"]

if "cat_id" not in st.session_state:
    st.session_state.cat_id = active_prof["catalog_id"]

st.title("🌌 Ricerca Siti Astronomici Bui (SQM & Tempi Auto)")
st.caption("✨ Dedicato con stima agli [**Astrofili Ponte di Piave**](https://www.astrofilipontedipiave.it/) Ponte di Piave (TV). Scritto da **R.D.M** - [Astrofili Ponte di Piave](https://www.astrofilipontedipiave.it/).")

st.markdown(
    f"""
    Questo strumento supera il limite della ricerca "in linea d'aria" di *LightPollutionMap*,
    valutando l'**effettiva raggiungibilità in auto** (tempi di percorrenza e distanze reali su strada)
    e i valori fotometrici **SQM / Bortle** aggiornati dai server di *LightPollutionMap.info*.  
    Profilo attivo: **{active_prof['name']}** — {active_prof['description']}
    """
)

# ----------------- SIDEBAR -----------------
st.sidebar.header("🏢 Profilo Territoriale")
profile_options = list_profiles()
prof_labels = list(profile_options.keys())
current_prof_label = next((lbl for lbl, pid in profile_options.items() if pid == st.session_state.active_profile), prof_labels[0])

selected_profile_label = st.sidebar.selectbox(
    "Area di riferimento:",
    options=prof_labels,
    index=prof_labels.index(current_prof_label),
    help="Passa istantaneamente da un'area territoriale all'altra impostando partenza e catalogo dedicati.",
    key="profile_selector"
)
chosen_prof_id = profile_options[selected_profile_label]
if chosen_prof_id != st.session_state.active_profile:
    st.session_state.active_profile = chosen_prof_id
    new_prof = get_profile(chosen_prof_id)
    st.session_state.origin_name = new_prof["default_origin"]["name"]
    st.session_state.origin_lat = new_prof["default_origin"]["lat"]
    st.session_state.origin_lon = new_prof["default_origin"]["lon"]
    st.session_state.test_name = new_prof["default_test"]["name"]
    st.session_state.test_lat = new_prof["default_test"]["lat"]
    st.session_state.test_lon = new_prof["default_test"]["lon"]
    st.session_state.cat_id = new_prof["catalog_id"]
    for k in ["catalog_selector", "origin_select_box", "origin_search_input"]:
        if k in st.session_state:
            del st.session_state[k]
    st.rerun()

active_prof = get_profile(st.session_state.active_profile)

st.sidebar.header("📍 Punto di Partenza")

# Barra di ricerca automatica della località di partenza
search_query = st.sidebar.text_input(
    "🔍 Cerca Partenza",
    placeholder="Città, Passo, Vetta, link Maps o GPS...",
    help="Puoi digitare città, comuni, passi alpini, vette, rifugi, incollare un link Google Maps o coordinate GPS.",
    key="origin_search_input"
)

if search_query:
    with st.sidebar:
        with st.spinner("Ricerca in corso..."):
            found = search_locations(search_query)
            if found:
                options = {}
                for idx, p in enumerate(found, 1):
                    lbl = f"📍 {p['name']}"
                    if lbl in options:
                        lbl = f"{lbl} (#{idx})"
                    options[lbl] = p
                selected_label = st.selectbox(
                    "Seleziona tra i risultati:",
                    options=list(options.keys()),
                    key="origin_select_box"
                )
                if st.button("✅ Imposta questa partenza", width="stretch"):
                    chosen = options[selected_label]
                    st.session_state.origin_name = chosen.get("display_name") or chosen["name"]
                    st.session_state.origin_lat = chosen["lat"]
                    st.session_state.origin_lon = chosen["lon"]
                    st.rerun()
            else:
                st.caption("⚠️ Nessuna località trovata. Puoi incollare direttamente un link Google Maps o coordinate GPS.")

st.sidebar.markdown(f"**Partenza attiva:**  \n📍 `{st.session_state.origin_name}`")
st.sidebar.caption(f"Coordinate: `{st.session_state.origin_lat:.4f}, {st.session_state.origin_lon:.4f}`")

# Pulsante di ripristino rapido alla partenza predefinita del profilo attivo
default_origin_name = active_prof["default_origin"]["name"]
if st.session_state.origin_name != default_origin_name:
    if st.sidebar.button(f"🔄 Ripristina {default_origin_name}", width="stretch"):
        st.session_state.origin_name = active_prof["default_origin"]["name"]
        st.session_state.origin_lat = active_prof["default_origin"]["lat"]
        st.session_state.origin_lon = active_prof["default_origin"]["lon"]
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

st.sidebar.header("📚 Catalogo Attivo")
cat_id = active_prof["catalog_id"]
selected_catalog_name = active_prof["catalog_name"]
st.sidebar.markdown(f"📍 **{selected_catalog_name}**")
st.sidebar.caption(f"Catalogo astronomico attivo per il profilo **{active_prof['name']}**.")

# Tributo Astrofili Ponte di Piave nel footer della sidebar
st.sidebar.divider()
logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo_astrofili_ponte_di_piave.png")
col_logo, col_tribute = st.sidebar.columns([1, 3])
with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, width=54)
with col_tribute:
    st.markdown(
        """
        <div style="font-size: 0.78rem; line-height: 1.35; color: #9ca3af;">
            Dedicato con stima agli<br>
            <b style="color: #60a5fa;"><a href="https://www.astrofilipontedipiave.it/" target="_blank" style="color: #60a5fa; text-decoration: none;">Astrofili Ponte di Piave</a></b><br>
            <span style="font-size: 0.72rem; color: #6b7280;">Ponte di Piave (TV)</span><br>
            <div style="margin-top: 4px; font-size: 0.72rem; color: #9ca3af;">Scritto da <b>R.D.M</b> - <a href="https://www.astrofilipontedipiave.it/" target="_blank" style="color: #60a5fa; text-decoration: none;">Astrofili Ponte di Piave</a></div>
        </div>
        """,
        unsafe_allow_html=True
    )

# ----------------- CARICAMENTO DATI SITI (ISTANTANEO) -----------------
@st.cache_data(ttl=3600)
def get_sites_data(lat, lon, origin_label, catalog_id):
    sites = load_catalog(catalog_id)
    return calculate_routes_for_origin(lat, lon, origin_label, sites=sites)

sites_data = get_sites_data(st.session_state.origin_lat, st.session_state.origin_lon, st.session_state.origin_name, cat_id)

# ----------------- TABS -----------------
tab_ranking, tab_test_point, tab_map_view = st.tabs(["🏆 Classifica Siti Bui", "🔍 Testa un Punto Personalizzato", "🗺️ Mappa Interattiva"])

with tab_ranking:
    st.subheader(f"📍 Tutti i Siti di Osservazione Ordinati per Tempo di Guida da {st.session_state.origin_name}")
    st.write(f"Trovati **{len(sites_data)}** siti nel catalogo **{selected_catalog_name}**, ordinati dal più vicino al più lontano.")
    
    table_rows = []
    for idx, s in enumerate(sites_data, 1):
        gmaps = s.get("gmaps_url", "")
        # Incorpora il nome della località nell'URL hash per estrazione pulita tramite LinkColumn
        link_url = f"{gmaps}#loc={s['name']}"
        table_rows.append({
            "#": idx,
            "Località": link_url,
            "Area": s.get("macro_region", "Altro"),
            "Zona": s["region"],
            "SQM 2025": s.get("sqm_2025", 0.0),
            "Quota (m)": int(s.get("elevation_m", 0)),
            "Tempo Auto": s.get("duration_str", "N/D"),
            "Distanza (km)": s.get("distance_km", 0.0),
            "Bortle": s.get("bortle", "N/D"),
            "Google Maps": gmaps
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
            column_config={
                "Località": st.column_config.LinkColumn(
                    "Località 🧭",
                    help="Clicca sul nome della località per aprire l'itinerario in Google Maps",
                    display_text=r"#loc=(.*)$"
                )
            },
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
        "🔎 Cerca località di destinazione",
        placeholder="Es. Passo Pramollo, Sonnleitn, Meduno, link Maps o GPS...",
        help="Trova qualsiasi città, comune, valico alpino, monte, rifugio, o incolla un link Google Maps o coordinate GPS.",
        key="test_search_input"
    )
    if test_search:
        with st.spinner("Ricerca località in corso..."):
            test_found = search_locations(test_search)
            if test_found:
                test_opts = {}
                for idx, p in enumerate(test_found, 1):
                    lbl = f"📍 {p['name']}"
                    if lbl in test_opts:
                        lbl = f"{lbl} (#{idx})"
                    test_opts[lbl] = p
                selected_test = st.selectbox("Seleziona tra i risultati:", options=list(test_opts.keys()))
                if st.button("📥 Usa queste coordinate per il test"):
                    c_test = test_opts[selected_test]
                    st.session_state.test_name = c_test.get("display_name") or c_test["name"]
                    st.session_state.test_lat = c_test["lat"]
                    st.session_state.test_lon = c_test["lon"]
                    st.rerun()
            else:
                st.caption("Nessuna destinazione trovata. Puoi incollare direttamente un link Google Maps o coordinate GPS.")

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
    st.write(f"La mappa visualizza tutti i **{len(sites_data)}** siti astronomici censiti nel catalogo **{selected_catalog_name}**.")
    try:
        map_html = generate_interactive_html(
            sites_data,
            {"name": st.session_state.origin_name, "lat": st.session_state.origin_lat, "lon": st.session_state.origin_lon},
            title=f"Mappa Siti Astronomici - {selected_catalog_name}"
        )
        if hasattr(st, "iframe"):
            st.iframe(map_html, height=750, width="stretch")
        else:
            st.components.v1.html(map_html, height=750, scrolling=True)
    except Exception as e:
        st.error(f"Impossibile generare la mappa: {e}")

st.divider()
st.markdown(
    """
    <div style="text-align: center; font-size: 0.85rem; color: #6b7280; padding: 8px 0;">
        Dedicato con stima agli <a href="https://www.astrofilipontedipiave.it/" target="_blank" style="color: #60a5fa; text-decoration: none; font-weight: 600;">Astrofili Ponte di Piave</a> — Ponte di Piave (TV).<br>
        Scritto da <b>R.D.M</b> - <a href="https://www.astrofilipontedipiave.it/" target="_blank" style="color: #60a5fa; text-decoration: none;">Astrofili Ponte di Piave</a>.
    </div>
    """,
    unsafe_allow_html=True
)
