"""
SQM Search & Driving Reachability Tool
Analisi siti con elevato SQM (> 21.7) e calcolo tempo reale di percorrenza in auto da Ghirano di Prata (PN).
Dati SQM interrogati direttamente dai server di LightPollutionMap.info (modelli SB 2025 e World Atlas 2015).
Distanze e tempi di guida calcolati tramite motore OSRM (Open Source Routing Machine).
"""

import base64
import time
import math
import json
import requests
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple

# Coordinate di partenza predefinite: Ghirano di Prata di Pordenone (PN)
DEFAULT_ORIGIN = {
    "name": "Ghirano di Prata (PN)",
    "lat": 45.8617,
    "lon": 12.5539
}

# Catalogo di siti montani con accesso stradale verificato
CURATED_SITES = [
    {
        "name": "Casera Razzo / Passo Ciampigotto",
        "lat": 46.4795,
        "lon": 12.5855,
        "region": "Cadore / Carnia (BL/UD)",
        "access": "Strada provinciale SP619 asfaltata. Ampio piazzale/parcheggio in piano (Rif. Tenente Fabbro / Malga Razzo). Sito storico Star Party Astrofili Triveneti. Orizzonte aperto a 360°, quota elevatissima sopra inversioni termiche.",
        "paved": True
    },
    {
        "name": "Passo Monte Croce Comelico",
        "lat": 46.6561,
        "lon": 12.4208,
        "region": "Comelico Superiore / Sesto (BL/BZ)",
        "access": "Strada Statale SS52 Carnica, molto ampia e sempre aperta. Diversi parcheggi lungo il valico e presso il centro fondo. Cielo nord e est scurissimo al confine con l'Alto Adige.",
        "paved": True
    },
    {
        "name": "Val Visdende (Pradon del Ghelp)",
        "lat": 46.5667,
        "lon": 12.6500,
        "region": "San Pietro di Cadore (BL)",
        "access": "Strada asfaltata da San Pietro di Cadore. Ampie radure e parcheggi. Valle alpina isolata, zero inquinamento luminoso locale, protetta da alte pareti rocciose.",
        "paved": True
    },
    {
        "name": "Pradibosco / Sella di Razzo (Val Pesarina)",
        "lat": 46.5167,
        "lon": 12.6667,
        "region": "Prato Carnico (UD)",
        "access": "SR465 della Val Pesarina. Parcheggi presso Pian di Casa e centro fondo. Valle appartata e tranquilla senza traffico notturno.",
        "paved": True
    },
    {
        "name": "Passo Valparola (Forte Tre Sassi)",
        "lat": 46.5278,
        "lon": 11.9902,
        "region": "Livinallongo / Badia (BL/BZ)",
        "access": "SP24 del Passo Valparola (accanto al Passo Falzarego). Enorme piazzale asfaltato presso il Forte Tre Sassi a quasi 2200m di quota. Trasparenza eccellente, sopra lo strato limite.",
        "paved": True
    },
    {
        "name": "Lago d'Antorno (Misurina)",
        "lat": 46.5942,
        "lon": 12.2597,
        "region": "Auronzo / Misurina (BL)",
        "access": "SP49 circa 1.5 km a nord del Lago di Misurina. Ampio piazzale asfaltato/ghiaia in riva al laghetto prima del casello per le Tre Cime. Schermato da luci dirette, cielo zenitale limpidissimo.",
        "paved": True
    },
    {
        "name": "Passo Tre Croci",
        "lat": 46.5819,
        "lon": 12.2558,
        "region": "Cortina d'Ampezzo / Auronzo (BL)",
        "access": "SR48 delle Dolomiti. Varie piazzole e parcheggi sterrati/asfaltati al valico tra il Cristallo e il Sorapis.",
        "paved": True
    },
    {
        "name": "Rifugio Auronzo (Tre Cime di Lavaredo)",
        "lat": 46.6124,
        "lon": 12.2952,
        "region": "Auronzo di Cadore (BL)",
        "access": "Strada panoramica a pedaggio (aperta da fine maggio a fine ottobre/novembre). Grandi piazzali asfaltati a 2320m sotto la parete sud delle Tre Cime. Buio d'alta quota e seeing eccezionale.",
        "paved": True
    },
    {
        "name": "Altopiano del Montasio (Malga Montasio)",
        "lat": 46.4161,
        "lon": 13.4219,
        "region": "Chiusaforte / Sella Nevea (UD)",
        "access": "Strada asfaltata panoramica che sale da Sella Nevea fino al parcheggio della Malga Montasio. Orizzonte sud completamente libero e aperto verso le Giulie, protetto a nord dal massiccio del Montasio.",
        "paved": True
    },
    {
        "name": "Passo Monte Croce Carnico (Plöckenpass)",
        "lat": 46.6033,
        "lon": 12.9444,
        "region": "Paluzza / confine Austria (UD)",
        "access": "SS52bis comoda e asfaltata. Ampio parcheggio all'ex valico di confine. Buio notevole verso nord e cielo montano molto limpido.",
        "paved": True
    },
    {
        "name": "Rifugio Tolazzi (Forni Avoltri / Collina)",
        "lat": 46.5911,
        "lon": 12.8358,
        "region": "Forni Avoltri (UD)",
        "access": "Strada comunale asfaltata da Rigolato/Collina. Grande parcheggio terminale ai piedi del Monte Coglians. Valle chiusa senza inquinamento luminoso.",
        "paved": True
    },
    {
        "name": "Passo delle Erbe (Würzjoch)",
        "lat": 46.6744,
        "lon": 11.8133,
        "region": "San Martino in Badia (BZ)",
        "access": "SP29 panoramica asfaltata. Grande parcheggio al valico sotto il Sass de Putia. Noto punto di osservazione astronomica dolomitico.",
        "paved": True
    },
    # Siti di compromesso veloci (SQM 21.55 - 21.68 ma tempi guida più brevi: 1h15 - 1h35)
    {
        "name": "Passo Cibiana",
        "lat": 46.3756,
        "lon": 12.2583,
        "region": "Valle di Cadore / Forno di Zoldo (BL)",
        "access": "SP347 del Passo Cibiana asfaltata. Parcheggi presso il valico (Rifugio Remauro). Raggiungibile in soli ~1h 24m da Ghirano!",
        "paved": True
    },
    {
        "name": "Passo Duran",
        "lat": 46.3253,
        "lon": 12.0945,
        "region": "Val di Zoldo / Agordo (BL)",
        "access": "SP347 asfaltata tra Zoldo e Agordo. Piazzale presso Rifugio San Sebastiano / Cesare Tomè. Raggiungibile in ~1h 27m, buio notevole tra Civetta e San Sebastiano.",
        "paved": True
    },
    {
        "name": "Passo Staulanza",
        "lat": 46.4215,
        "lon": 12.1039,
        "region": "Val di Zoldo / Selva di Cadore (BL)",
        "access": "SP251 asfaltata. Piazzale al valico tra Pelmo e Civetta a 1766m. Raggiungibile in ~1h 32m, SQM ~21.62.",
        "paved": True
    },
    {
        "name": "Passo Mauria",
        "lat": 46.4608,
        "lon": 12.5292,
        "region": "Lorenzago di Cadore / Forni di Sopra (BL/UD)",
        "access": "SS52 comoda e ampia. Parcheggi al valico a 1298m. SQM ~21.67 in ~1h 48m.",
        "paved": True
    },
    {
        "name": "Val Cimoliana (Pian Meluzzo / Rif. Pordenone)",
        "lat": 46.3888,
        "lon": 12.5135,
        "region": "Cimolais / Parco Dolomiti Friulane (PN)",
        "access": "Val Cimoliana dal centro di Cimolais: strada asfaltata nel primo tratto poi sterrata/ghiaiosa fino a Pian Meluzzo (Rifugio Pordenone). Luogo selvaggio nel cuore del Parco, SQM ~21.65 - 21.70. Attenzione al fondo stradale ghiaioso nell'ultimo tratto.",
        "paved": False
    },
    {
        "name": "Passo Giau",
        "lat": 46.4825,
        "lon": 12.0538,
        "region": "Colle Santa Lucia / Cortina (BL)",
        "access": "SP638 panoramica asfaltata. Grandi piazzali a 2236m. Orizzonte a 360°, aria finissima, SQM ~21.65.",
        "paved": True
    },
    {
        "name": "Passo Rest",
        "lat": 46.3533,
        "lon": 12.8392,
        "region": "Tramonti di Sopra / Priuso (PN/UD)",
        "access": "SP552 asfaltata ma stretta e con molti tornanti. Piazzole al valico a 1052m. Valle selvaggia e isolata, SQM ~21.52 - 21.58.",
        "paved": True
    },
    {
        "name": "Passo Sant'Osvaldo (Erto)",
        "lat": 46.2750,
        "lon": 12.3833,
        "region": "Erto e Casso / Vajont (PN)",
        "access": "SR251 comoda attraverso la Valcellina. Piazzali a Erto e presso la diga del Vajont. Raggiungibile in ~1h 09m, SQM ~21.43.",
        "paved": True
    },
    {
        "name": "Piancavallo (Castaldia)",
        "lat": 46.1083,
        "lon": 12.5083,
        "region": "Aviano (PN)",
        "access": "SP31 veloce da Aviano. Parcheggio dorsale Castaldia a 1470m. Raggiungibile in ~56m! SQM ~21.08 (buono verso nord, ma disturbo della pianura verso sud).",
        "paved": True
    },
    {
        "name": "Cansiglio (Pian Osteria)",
        "lat": 46.0694,
        "lon": 12.4042,
        "region": "Alpago / Tambre (BL)",
        "access": "SP422 veloce da Caneva o Vittorio Veneto. Ampio pianoro dell'altopiano del Cansiglio a 1000m, parcheggi in piano. Raggiungibile in soli ~50m da Ghirano! SQM ~21.04.",
        "paved": True
    },
    {
        "name": "Pala Barzana",
        "lat": 46.2333,
        "lon": 12.7333,
        "region": "Andreis / Poffabro (PN)",
        "access": "SP26 della Pala Barzana. Valico a 640m-840m tra Valcellina e Val Colvera. Zona appartata a ~60m da Ghirano. SQM ~21.25.",
        "paved": True
    },
    {
        "name": "Alpe del Nevegal (Piazzale)",
        "lat": 46.0917,
        "lon": 12.2833,
        "region": "Belluno (BL)",
        "access": "SP31 comoda da Belluno/Cadola. Grandi piazzali asfaltati a 1080m con vista aperta a nord sulle Dolomiti Bellunesi. Raggiungibile in ~1h 02m. SQM ~21.03.",
        "paved": True
    },
    {
        "name": "Passo San Boldo",
        "lat": 46.0078,
        "lon": 12.1706,
        "region": "Cison di Valmarino / Trichiana (TV/BL)",
        "access": "SP635 dei 100 giorni. Parcheggi al valico a 706m. Raggiungibile in ~55m. SQM ~20.75.",
        "paved": True
    },
    {
        "name": "Monte Cesen (Malga Mariech)",
        "lat": 45.9292,
        "lon": 12.0167,
        "region": "Valdobbiadene (TV)",
        "access": "Strada panoramica asfaltata fino alla sommità del Monte Cesen / Malga Mariech a 1500m. Grande piazzale con orizzonte aperto. Raggiungibile in ~1h 15m. SQM ~20.85.",
        "paved": True
    },
    {
        "name": "Cima Grappa (Rifugio Bassano)",
        "lat": 45.8722,
        "lon": 11.8028,
        "region": "Monte Grappa (TV/VI/BL)",
        "access": "SP140 Strada Cadorna. Vasto piazzale asfaltato a quasi 1800m. Quota elevata sopra le nebbie della pianura. Raggiungibile in ~1h 30m. SQM ~20.90.",
        "paved": True
    },
    {
        "name": "Sella Chianzutan",
        "lat": 46.3750,
        "lon": 12.9667,
        "region": "Verzegnis (UD)",
        "access": "SP1 comoda e asfaltata tra Tolmezzo e la Val d'Arzino. Piazzale al valico a 955m. Raggiungibile in ~1h 38m. SQM ~21.37.",
        "paved": True
    },
    {
        "name": "Val Canzoi (Lago della Stua)",
        "lat": 46.1550,
        "lon": 11.9750,
        "region": "Cesiomaggiore / Dolomiti Bellunesi (BL)",
        "access": "Strada asfaltata fino al parcheggio della Val Canzoi (Parco Nazionale Dolomiti Bellunesi). Valle stretta e riparata. SQM ~21.37 in ~1h 46m.",
        "paved": True
    },
    {
        "name": "Passo Pramollo (Nassfeld)",
        "lat": 46.5644,
        "lon": 13.2756,
        "region": "Pontebba / Carinzia (UD/A)",
        "access": "SP110 da Pontebba. Valico alpino a 1530m con ampi parcheggi all'ex confine. Buio notevole sulle Alpi Carniche orientali. SQM ~21.76.",
        "paved": True
    },
    {
        "name": "Laghi di Fusine (Lago Superiore)",
        "lat": 46.4789,
        "lon": 13.6708,
        "region": "Tarvisio (UD)",
        "access": "Strada asfaltata da Fusine in Valromana fino al parcheggio del Lago Superiore a 956m. Orizzonte sud verso la parete nord del Mangart, luogo suggestivo e molto buio. SQM ~21.69.",
        "paved": True
    },
    {
        "name": "Val Saisera (Malga Saisera)",
        "lat": 46.4833,
        "lon": 13.4833,
        "region": "Malborghetto-Valbruna (UD)",
        "access": "Strada asfaltata lungo la Val Saisera fino ai parcheggi terminali sotto il Jôf Fuart e Jôf di Montasio a 990m. Molto riparata dalle luci. SQM ~21.67.",
        "paved": True
    },
    {
        "name": "Sella Nevea (Piazzale Rif. Gilberti)",
        "lat": 46.3889,
        "lon": 13.4806,
        "region": "Chiusaforte (UD)",
        "access": "SP76 asfaltata. Ampi piazzali di sosta a 1210m tra il Montasio e il massiccio del Canin. SQM ~21.69.",
        "paved": True
    },
    {
        "name": "Valle Vecchia / Brussa (Caorle)",
        "lat": 45.6267,
        "lon": 12.9617,
        "region": "Caorle / Valle Vecchia (VE)",
        "access": "Strada provinciale della Brussa fino al grande parcheggio dell'oasi naturale di Valle Vecchia. L'area costiera più buia dell'Alto Adriatico: nessuna urbanizzazione né lampioni, orizzonte sud aperto sul mare! Raggiungibile in soli ~1h 05m (60 km) da Ghirano. SQM ~20.91.",
        "paved": True
    },
    {
        "name": "Foce del Tagliamento (Bibione Pineda)",
        "lat": 45.6428,
        "lon": 13.0967,
        "region": "San Michele al Tagliamento (VE)",
        "access": "Parcheggio terminale verso l'area naturale della foce del Tagliamento e faro. Orizzonte marino verso sud con ridotto inquinamento luminoso diretto. SQM ~20.70.",
        "paved": True
    },
    {
        "name": "Monte Zoncolan (Piazzale Vetta)",
        "lat": 46.5014,
        "lon": 12.9286,
        "region": "Sutrio / Ovaro (UD)",
        "access": "Strada asfaltata da Sutrio o da Ovaro. Grande piazzale al valico a 1730m. Panorama a 360° sulla Carnia, sopra le inversioni termiche. SQM ~21.62.",
        "paved": True
    },
    {
        "name": "Sella Carnizza (Val Resia)",
        "lat": 46.3458,
        "lon": 13.3167,
        "region": "Resia / Lusevera (UD)",
        "access": "SP42 asfaltata. Valico a 1086m tra Val Resia e Alta Val Torre. Zona silenziosa e schermata dalle luci di pianura e fondovalle. SQM ~21.56.",
        "paved": True
    },
    {
        "name": "Passo Falzarego",
        "lat": 46.5186,
        "lon": 12.0089,
        "region": "Cortina d'Ampezzo / Livinallongo (BL)",
        "access": "SR48 delle Dolomiti. Ampio piazzale al valico a 2105m sotto il Sass de Stria e il Lagazuoi. Trasparenza eccellente. SQM ~21.71.",
        "paved": True
    },
    {
        "name": "Passo San Pellegrino",
        "lat": 46.3778,
        "lon": 11.7892,
        "region": "Falcade / Moena (BL/TN)",
        "access": "SS346 comoda e ampia. Parcheggi al valico a 1918m tra Veneto e Trentino. SQM ~21.62.",
        "paved": True
    },
    {
        "name": "Passo Valles",
        "lat": 46.3392,
        "lon": 11.7828,
        "region": "Falcade / Paneveggio (BL/TN)",
        "access": "SP81 asfaltata. Piazzale al valico a 2032m sotto le Pale di San Martino. SQM ~21.61.",
        "paved": True
    },
    {
        "name": "Passo Rolle",
        "lat": 46.2967,
        "lon": 11.7878,
        "region": "Primiero / Paneveggio (TN)",
        "access": "SS50 comoda. Grandi piazzali a 1989m con vista iconica sulle Pale di San Martino e il Cimon della Pala. SQM ~21.57.",
        "paved": True
    },
    {
        "name": "Passo Fedaia (Diga / Marmolada)",
        "lat": 46.4567,
        "lon": 11.8864,
        "region": "Rocca Pietore / Canazei (BL/TN)",
        "access": "SP641 asfaltata. Grandi piazzali lungo il lago e la diga ai piedi della Marmolada a 2057m. SQM ~21.66.",
        "paved": True
    },
    {
        "name": "Sauris di Sopra (Sella Festons)",
        "lat": 46.4750,
        "lon": 12.6833,
        "region": "Sauris (UD)",
        "access": "Strada panoramica asfaltata da Sauris di Sopra verso Sella Festons a 1730m. Buio di alta montagna nel cuore della Carnia. SQM ~21.69.",
        "paved": True
    }
]


def search_locations(query: str) -> List[Dict]:
    """
    Cerca le coordinate geografiche (lat, lon) a partire dal nome di una città, comune o indirizzo.
    Utilizza OpenStreetMap Nominatim con fallback su Open-Meteo Geocoding.
    """
    if not query or len(query.strip()) < 2:
        return []
    
    results = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    # 1. OpenStreetMap Nominatim
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(query)}&format=json&limit=5&countrycodes=it,si,at,ch"
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            for item in resp.json():
                display = item.get("display_name", "")
                parts = [p.strip() for p in display.split(",")]
                short_name = ", ".join(parts[:3]) if len(parts) >= 3 else display
                results.append({
                    "name": short_name,
                    "full_name": display,
                    "lat": round(float(item["lat"]), 5),
                    "lon": round(float(item["lon"]), 5)
                })
    except Exception:
        pass

    # 2. Fallback su Open-Meteo Geocoding
    if not results:
        try:
            url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(query)}&count=5&language=it"
            resp = requests.get(url, timeout=6)
            if resp.status_code == 200:
                for r in resp.json().get("results", []):
                    parts = [r.get("name"), r.get("admin1"), r.get("country")]
                    name_str = ", ".join([p for p in parts if p])
                    results.append({
                        "name": name_str,
                        "full_name": name_str,
                        "lat": round(float(r["latitude"]), 5),
                        "lon": round(float(r["longitude"]), 5)
                    })
        except Exception:
            pass

    return results


def generate_lpm_token() -> str:
    """Genera il token di sessione per l'API di lightpollutionmap.info."""
    now_ms = int(time.time() * 1000)
    raw = f"{now_ms};isuckdicks:)"
    return base64.b64encode(raw.encode()).decode()


def query_lpm_point(lat: float, lon: float, qk: Optional[str] = None) -> Dict:
    """
    Interroga i raster di lightpollutionmap.info per il punto (lat, lon).
    Restituisce SQM 2025, SQM 2015, elevazione, radianza artificiale e classe Bortle.
    """
    if not qk:
        qk = generate_lpm_token()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.lightpollutionmap.info/"
    }

    results = {
        "sqm_2025": None,
        "sqm_2015": None,
        "elevation_m": None,
        "bortle": None,
        "nelm": None,
        "raw_v_2025": None
    }

    # 1. Query SB 2025
    try:
        url_2025 = f"https://www.lightpollutionmap.info/api/queryraster?qk={qk}&ql=sb_2025&qt=point&qd={lon},{lat}"
        r25 = requests.get(url_2025, headers=headers, timeout=10).text
        parts25 = r25.split(',')
        v25 = float(parts25[0].split(';')[-1])
        elev = float(parts25[1]) if len(parts25) > 1 and parts25[1] else 0.0
        
        # Formula Falchi et al. / LightPollutionMap
        sqm25 = math.log10((v25 + 0.171168465) / 108e6) / -0.4
        nelm = 7.93 - 5 * math.log10(math.pow(10, 4.316 - sqm25 / 5) + 1)
        
        results["sqm_2025"] = round(sqm25, 2)
        results["elevation_m"] = round(elev, 0)
        results["nelm"] = round(nelm, 2)
        results["raw_v_2025"] = v25
        
        # Classe Bortle ufficiale LPM
        if sqm25 < 18.38:
            bortle = "Classe 8-9 (Città)"
        elif sqm25 < 18.94:
            bortle = "Classe 7 (Transizione periurbana)"
        elif sqm25 < 19.50:
            bortle = "Classe 6 (Cielo suburbano luminoso)"
        elif sqm25 < 20.49:
            bortle = "Classe 5 (Cielo suburbano)"
        elif sqm25 < 21.69:
            bortle = "Classe 4 (Transizione rurale/suburbana)"
        elif sqm25 < 21.89:
            bortle = "Classe 3 (Cielo rurale)"
        elif sqm25 < 21.99:
            bortle = "Classe 2 (Cielo buio tipico)"
        else:
            bortle = "Classe 1 (Cielo buio eccellente)"
        results["bortle"] = bortle
    except Exception as e:
        pass

    # 2. Query WA 2015 (World Atlas)
    try:
        url_2015 = f"https://www.lightpollutionmap.info/api/queryraster?qk={qk}&ql=wa_2015&qt=point&qd={lon},{lat}"
        r15 = requests.get(url_2015, headers=headers, timeout=10).text
        parts15 = r15.split(',')
        v15 = float(parts15[0].split(';')[-1])
        sqm15 = math.log10((v15 + 0.171168465) / 108e6) / -0.4
        results["sqm_2015"] = round(sqm15, 2)
    except Exception:
        pass

    return results


def query_driving_route(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> Dict:
    """
    Calcola l'itinerario reale in auto tramite motore OSRM (Open Source Routing Machine).
    Restituisce distanza in km, durata in minuti, e percorso per polyline.
    """
    url = f"http://router.project-osrm.org/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}?overview=full&geometries=geojson"
    try:
        resp = requests.get(url, headers={"User-Agent": "SqmSearchTool/1.0"}, timeout=12).json()
        if resp.get("code") == "Ok" and resp.get("routes"):
            route = resp["routes"][0]
            dist_km = route["distance"] / 1000.0
            dur_min = route["duration"] / 60.0
            geometry = route["geometry"]
            return {
                "success": True,
                "distance_km": round(dist_km, 1),
                "duration_min": round(dur_min, 0),
                "duration_str": f"{int(dur_min // 60)}h {int(dur_min % 60):02d}m",
                "geometry": geometry
            }
    except Exception as e:
        pass

    # Fallback in caso di mancata risposta del server
    return {
        "success": False,
        "distance_km": 0,
        "duration_min": 999,
        "duration_str": "N/D",
        "geometry": None
    }


def evaluate_all_sites(origin: Optional[Dict] = None, min_sqm: float = 20.0) -> List[Dict]:
    """
    Valuta l'intero catalogo di siti rispetto al punto di origine e alla soglia SQM.
    """
    if not origin:
        origin = DEFAULT_ORIGIN

    qk = generate_lpm_token()
    results = []

    print(f"Calcolo itinerari e interrogazione SQM da {origin['name']} (lat: {origin['lat']}, lon: {origin['lon']})...")
    for site in CURATED_SITES:
        # LPM
        lpm_data = query_lpm_point(site["lat"], site["lon"], qk=qk)
        # OSRM
        route_data = query_driving_route(origin["lat"], origin["lon"], site["lat"], site["lon"])
        
        sqm_val = lpm_data["sqm_2025"] if lpm_data["sqm_2025"] is not None else 0.0
        
        gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin['lat']},{origin['lon']}&destination={site['lat']},{site['lon']}&travelmode=driving"
        
        entry = {
            "name": site["name"],
            "region": site["region"],
            "lat": site["lat"],
            "lon": site["lon"],
            "elevation_m": lpm_data["elevation_m"],
            "sqm_2025": lpm_data["sqm_2025"],
            "sqm_2015": lpm_data["sqm_2015"],
            "nelm": lpm_data["nelm"],
            "bortle": lpm_data["bortle"],
            "distance_km": route_data["distance_km"],
            "duration_min": route_data["duration_min"],
            "duration_str": route_data["duration_str"],
            "access": site["access"],
            "paved": site["paved"],
            "gmaps_url": gmaps_url,
            "geometry": route_data.get("geometry")
        }
        
        if sqm_val >= min_sqm:
            results.append(entry)
            
        time.sleep(0.15) # Pausa cortese tra le richieste API

    # Ordina per tempo di guida
    results.sort(key=lambda x: x["duration_min"])
    return results


def export_interactive_html(results: List[Dict], origin: Dict, output_path: str = "sqm_dark_sites_map.html"):
    """
    Crea una mappa interattiva HTML moderna con Leaflet.js,
    con marker colorati, itinerari tracciati, popup dettagliati e link a Google Maps.
    """
    origin_json = json.dumps(origin)
    sites_json = json.dumps(results)

    html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>Mappa Siti Astronomici Bui (SQM > 21.7) da Ghirano di Prata</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #111827;
            color: #f3f4f6;
        }}
        #header {{
            background: #1f2937;
            padding: 12px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid #374151;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }}
        #header h1 {{
            margin: 0;
            font-size: 1.15rem;
            font-weight: 600;
            color: #60a5fa;
        }}
        #header .subtitle {{
            font-size: 0.82rem;
            color: #9ca3af;
        }}
        #container {{
            display: flex;
            height: calc(100vh - 65px);
        }}
        #sidebar {{
            width: 420px;
            background: #111827;
            overflow-y: auto;
            border-right: 1px solid #374151;
            padding: 12px;
            box-sizing: border-box;
        }}
        #map {{
            flex: 1;
            height: 100%;
        }}
        .site-card {{
            background: #1f2937;
            border: 1px solid #374151;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .site-card:hover {{
            border-color: #3b82f6;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
        }}
        .site-card.active {{
            border-color: #60a5fa;
            background: #1e3a8a25;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 7px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: bold;
            margin-right: 5px;
        }}
        .badge-sqm-dark {{ background: #047857; color: #fff; }}
        .badge-sqm-high {{ background: #10b981; color: #fff; }}
        .badge-sqm-mid {{ background: #2563eb; color: #fff; }}
        .badge-sqm-violet {{ background: #7c3aed; color: #fff; }}
        .badge-sqm-amber {{ background: #d97706; color: #fff; }}
        .badge-time {{ background: #4b5563; color: #e5e7eb; }}
        .badge-alt {{ background: #4f46e5; color: #fff; }}
        .site-title {{
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 6px;
            color: #f9fafb;
        }}
        .site-region {{
            font-size: 0.78rem;
            color: #9ca3af;
            margin-bottom: 8px;
        }}
        .site-desc {{
            font-size: 0.8rem;
            color: #d1d5db;
            line-height: 1.35;
            margin-top: 6px;
        }}
        .nav-btn {{
            display: inline-block;
            margin-top: 8px;
            padding: 5px 10px;
            background: #2563eb;
            color: white;
            border-radius: 5px;
            text-decoration: none;
            font-size: 0.78rem;
            font-weight: 500;
            transition: background 0.2s;
        }}
        .nav-btn:hover {{
            background: #1d4ed8;
        }}
        .leaflet-popup-content-wrapper {{
            background: #1f2937 !important;
            color: #f3f4f6 !important;
            border-radius: 8px;
            border: 1px solid #374151;
        }}
        .leaflet-popup-tip {{
            background: #1f2937 !important;
        }}
    </style>
</head>
<body>
    <div id="header">
        <div>
            <h1>Siti di Osservazione Astronomica (SQM &gt; 20.0 &amp; Tempi Auto)</h1>
            <div class="subtitle">Partenza da Ghirano di Prata (PN) • Tempi reali stradali OSRM • Dati fotometrici LightPollutionMap</div>
        </div>
        <div style="font-size: 0.85rem; color: #10b981; font-weight: 600;">
            {len(results)} Localit&agrave; Analizzate
        </div>
    </div>
    <div id="container">
        <div id="sidebar">
            <div style="margin-bottom: 12px; font-size: 0.82rem; color: #9ca3af;">
                Ordinati per tempo di guida effettivo in auto da Ghirano di Prata:
            </div>
            <div id="cards-list"></div>
        </div>
        <div id="map"></div>
    </div>

    <script>
        const origin = {origin_json};
        const sites = {sites_json};

        // Inizializza mappa centrata tra Ghirano e le Dolomiti
        const map = L.map('map').setView([46.25, 12.35], 9);

        // Livelli di mappa 100% liberi SENZA alcuna API Key
        const osm = L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19
        }});

        const esriTopo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: 'Tiles &copy; Esri &mdash; Topo Relief',
            maxZoom: 18
        }});

        const esriSat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{
            attribution: 'Tiles &copy; Esri &mdash; World Imagery',
            maxZoom: 18
        }});

        // Imposta OpenStreetMap come livello predefinito
        osm.addTo(map);

        // Selettore livelli mappa in alto a destra (Stradale, Rilievo montano, Satellite)
        L.control.layers({{
            "Mappa Stradale (OpenStreetMap)": osm,
            "Rilievo Montano (Esri Topo)": esriTopo,
            "Satellite (Esri Imagery)": esriSat
        }}, null, {{ position: 'topright' }}).addTo(map);

        // Marker partenza Ghirano
        const originIcon = L.divIcon({{
            className: 'origin-marker',
            html: '<div style="background:#ef4444;border:2px solid white;border-radius:50%;width:16px;height:16px;box-shadow:0 0 8px rgba(239,68,68,0.8);"></div>',
            iconSize: [16, 16],
            iconAnchor: [8, 8]
        }});
        L.marker([origin.lat, origin.lon], {{icon: originIcon}}).addTo(map)
            .bindPopup(`<b>Punto di Partenza:</b><br>${{origin.name}}<br><small>Lat: ${{origin.lat}}, Lon: ${{origin.lon}}</small>`);

        const markers = [];
        const routeLayers = [];

        function getMarkerColor(sqm) {{
            if (sqm >= 21.75) return '#047857'; // Verde scuro top dark
            if (sqm >= 21.70) return '#10b981'; // Verde smeraldo
            if (sqm >= 21.50) return '#2563eb'; // Blu
            if (sqm >= 21.00) return '#7c3aed'; // Viola
            return '#d97706'; // Ambra / Arancio per SQM 20.0 - 20.99
        }}

        function getSqmBadgeClass(sqm) {{
            if (sqm >= 21.75) return 'badge-sqm-dark';
            if (sqm >= 21.70) return 'badge-sqm-high';
            if (sqm >= 21.50) return 'badge-sqm-mid';
            if (sqm >= 21.00) return 'badge-sqm-violet';
            return 'badge-sqm-amber';
        }}

        const cardsContainer = document.getElementById('cards-list');

        sites.forEach((site, idx) => {{
            const color = getMarkerColor(site.sqm_2025);
            const badgeClass = getSqmBadgeClass(site.sqm_2025);
            
            // Marker mappa
            const icon = L.divIcon({{
                className: 'custom-pin',
                html: `<div style="background:${{color}};border:2px solid white;border-radius:50%;width:22px;height:22px;display:flex;align-items:center;justify-content:center;color:white;font-size:10px;font-weight:bold;box-shadow:0 0 10px ${{color}}88;">${{idx + 1}}</div>`,
                iconSize: [22, 22],
                iconAnchor: [11, 11]
            }});

            const marker = L.marker([site.lat, site.lon], {{icon: icon}}).addTo(map);
            markers.push(marker);

            const popupContent = `
                <div style="font-family: sans-serif; min-width: 200px;">
                    <h3 style="margin: 0 0 4px 0; color: #60a5fa; font-size: 1rem;">${{idx + 1}}. ${{site.name}}</h3>
                    <div style="font-size: 0.8rem; color: #9ca3af; margin-bottom: 8px;">${{site.region}}</div>
                    <div style="margin-bottom: 6px;">
                        <span class="badge ${{badgeClass}}">SQM ${{site.sqm_2025}}</span>
                        <span class="badge badge-time">🚗 ${{site.duration_str}} (${{site.distance_km}} km)</span>
                    </div>
                    <div style="font-size: 0.8rem; margin-bottom: 4px;"><b>Quota:</b> ${{site.elevation_m}} m s.l.m.</div>
                    <div style="font-size: 0.8rem; margin-bottom: 4px;"><b>Bortle:</b> ${{site.bortle}}</div>
                    <div style="font-size: 0.78rem; color: #d1d5db; margin-top: 6px;">${{site.access}}</div>
                    <a class="nav-btn" href="${{site.gmaps_url}}" target="_blank">🧭 Naviga con Google Maps</a>
                </div>
            `;
            marker.bindPopup(popupContent);

            // Se disponibile la geometria del percorso OSRM, disegna linea
            if (site.geometry && site.geometry.coordinates) {{
                const latlngs = site.geometry.coordinates.map(coord => [coord[1], coord[0]]);
                const polyline = L.polyline(latlngs, {{
                    color: color,
                    weight: 3,
                    opacity: 0.65,
                    dashArray: '4, 8'
                }}).addTo(map);
                routeLayers.push(polyline);
            }}

            // Card laterale
            const card = document.createElement('div');
            card.className = 'site-card';
            card.innerHTML = `
                <div class="site-title">${{idx + 1}}. ${{site.name}}</div>
                <div class="site-region">${{site.region}}</div>
                <div style="margin-bottom: 6px;">
                    <span class="badge ${{badgeClass}}">SQM ${{site.sqm_2025}}</span>
                    <span class="badge badge-time">🚗 ${{site.duration_str}}</span>
                    <span class="badge badge-alt">🏔️ ${{site.elevation_m}}m</span>
                </div>
                <div style="font-size: 0.76rem; color: #9ca3af;">Distanza: ${{site.distance_km}} km • ${{site.bortle}}</div>
                <div class="site-desc">${{site.access}}</div>
                <a class="nav-btn" href="${{site.gmaps_url}}" target="_blank">🧭 Avvia Navigatore</a>
            `;

            card.addEventListener('click', () => {{
                document.querySelectorAll('.site-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                map.flyTo([site.lat, site.lon], 11, {{ duration: 1.2 }});
                marker.openPopup();
            }});

            cardsContainer.appendChild(card);
        }});

        // Gestore click su qualsiasi punto della mappa per calcolo istantaneo SQM e tempo auto
        let clickMarker = null;
        let clickRouteLayer = null;

        map.on('click', async function(e) {{
            const lat = e.latlng.lat;
            const lon = e.latlng.lng;

            if (clickMarker) map.removeLayer(clickMarker);
            if (clickRouteLayer) map.removeLayer(clickRouteLayer);

            const loadingPopup = L.popup()
                .setLatLng(e.latlng)
                .setContent('<div style="padding:10px;text-align:center;font-family:sans-serif;">⏳ <b>Calcolo in corso...</b><br><small style="color:#9ca3af;">Interrogazione SQM e tempo guida da ' + origin.name + '</small></div>')
                .openOn(map);

            try {{
                // 1. Interrogazione raster LPM per SQM e quota terreno
                const now = new Date().getTime();
                const qk = btoa(now + ";isuckdicks:)");
                const lpmUrl = "https://www.lightpollutionmap.info/api/queryraster?qk=" + qk + "&ql=sb_2025&qt=point&qd=" + lon.toFixed(5) + "," + lat.toFixed(5);
                
                let sqm = 0;
                let elev = 0;
                let bortle = "N/D";
                let nelm = "N/D";

                try {{
                    const lpmRes = await fetch(lpmUrl);
                    const lpmText = await lpmRes.text();
                    const parts = lpmText.split(',');
                    const v = parseFloat(parts[0].split(';').pop());
                    elev = parts[1] ? Math.round(parseFloat(parts[1])) : 0;

                    sqm = Math.log10((v + 0.171168465) / 108e6) / -0.4;
                    sqm = Math.round(sqm * 100) / 100;
                    nelm = (7.93 - 5 * Math.log10(Math.pow(10, 4.316 - sqm / 5) + 1)).toFixed(2);

                    if (sqm < 18.38) bortle = "Classe 8-9 (Città)";
                    else if (sqm < 18.94) bortle = "Classe 7 (Periurbano)";
                    else if (sqm < 19.50) bortle = "Classe 6 (Suburbano)";
                    else if (sqm < 20.49) bortle = "Classe 5 (Suburbano)";
                    else if (sqm < 21.69) bortle = "Classe 4 (Transizione)";
                    else if (sqm < 21.89) bortle = "Classe 3 (Rurale)";
                    else if (sqm < 21.99) bortle = "Classe 2 (Buio tipico)";
                    else bortle = "Classe 1 (Cielo eccellente)";
                }} catch(err) {{
                    console.error("LPM error:", err);
                }}

                // 2. Calcolo percorso stradale OSRM da punto di partenza
                let distKm = 0;
                let durStr = "N/D";
                const osrmUrl = "https://router.project-osrm.org/route/v1/driving/" + origin.lon + "," + origin.lat + ";" + lon.toFixed(5) + "," + lat.toFixed(5) + "?overview=full&geometries=geojson";

                try {{
                    const osrmRes = await fetch(osrmUrl);
                    const osrmData = await osrmRes.json();
                    if (osrmData.code === "Ok" && osrmData.routes && osrmData.routes.length > 0) {{
                        const r = osrmData.routes[0];
                        distKm = Math.round((r.distance / 1000) * 10) / 10;
                        const durMin = Math.round(r.duration / 60);
                        durStr = Math.floor(durMin / 60) + "h " + (durMin % 60) + "m (" + durMin + " min)";

                        const coords = r.geometry.coordinates.map(c => [c[1], c[0]]);
                        clickRouteLayer = L.polyline(coords, {{
                            color: '#f43f5e',
                            weight: 4,
                            opacity: 0.9,
                            dashArray: '6, 8'
                        }}).addTo(map);
                    }}
                }} catch(err) {{
                    console.error("OSRM error:", err);
                }}

                const badgeClass = getSqmBadgeClass(sqm);
                const gmapsUrl = "https://www.google.com/maps/dir/?api=1&origin=" + origin.lat + "," + origin.lon + "&destination=" + lat.toFixed(5) + "," + lon.toFixed(5) + "&travelmode=driving";

                const clickIcon = L.divIcon({{
                    className: 'click-pin',
                    html: '<div style="background:#f43f5e;border:2px solid white;border-radius:50%;width:24px;height:24px;display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:bold;box-shadow:0 0 14px rgba(244,63,94,1);">📍</div>',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                }});

                clickMarker = L.marker([lat, lon], {{ icon: clickIcon }}).addTo(map);
                map.closePopup(loadingPopup);

                const popupHtml = '<div style="font-family:sans-serif;min-width:230px;">' +
                    '<h3 style="margin:0 0 4px 0;color:#f43f5e;font-size:1.05rem;">📍 Punto Cliccato</h3>' +
                    '<div style="font-size:0.78rem;color:#9ca3af;margin-bottom:8px;">Coord: ' + lat.toFixed(4) + ', ' + lon.toFixed(4) + '</div>' +
                    '<div style="margin-bottom:6px;">' +
                        '<span class="badge ' + badgeClass + '">SQM ' + (sqm > 0 ? sqm.toFixed(2) : 'N/D') + '</span> ' +
                        '<span class="badge badge-time">🚗 ' + durStr + '</span>' +
                    '</div>' +
                    '<div style="font-size:0.8rem;margin-bottom:4px;"><b>Distanza stradale:</b> ' + (distKm > 0 ? distKm + ' km' : 'N/D') + '</div>' +
                    '<div style="font-size:0.8rem;margin-bottom:4px;"><b>Quota suolo:</b> ' + elev + ' m s.l.m.</div>' +
                    '<div style="font-size:0.8rem;margin-bottom:6px;"><b>Bortle:</b> ' + bortle + ' • <b>NELM:</b> ' + nelm + ' mag</div>' +
                    '<a class="nav-btn" style="background:#f43f5e;" href="' + gmapsUrl + '" target="_blank">🧭 Naviga verso questo punto</a>' +
                '</div>';

                clickMarker.bindPopup(popupHtml).openPopup();

            }} catch(e) {{
                loadingPopup.setContent('<div style="color:#ef4444;padding:8px;">Errore durante il calcolo. Riprova.</div>');
            }}
        }});
    </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Mappa interattiva generata con successo: {output_path}")


if __name__ == "__main__":
    results = evaluate_all_sites(min_sqm=20.0)
    export_interactive_html(results, DEFAULT_ORIGIN, "d:/ProgettiVari/SqmSearch/sqm_dark_sites_map.html")
