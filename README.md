# 🌌 SQM Search & Driving Reachability Tool

Uno strumento per individuare e valutare i **migliori siti di osservazione astronomica** (con qualità del cielo buio **SQM > 20.0** o personalizzabile) superando il limite della ricerca "in linea d'aria" di *LightPollutionMap*, integrando i **tempi di percorrenza e le distanze stradali reali in auto**.

Punto di partenza predefinito: **Ghirano di Prata (PN)** *(modificabile liberamente con ricerca automatica o coordinate manuali)*.

Copertura geografica estesa:
* 🇮🇹 **Friuli-Venezia Giulia** (21 siti: Carnia, Tarvisiano, Dolomiti e Prealpi Friulane, Valli del Natisone)
* 🇮🇹 **Veneto** (25 siti: Dolomiti Bellunesi, Cadore, Altopiano di Asiago, Monte Grappa, Lessinia)
* 🇮🇹 **Trentino-Alto Adige** (14 siti: Val Badia, Val di Fassa, Val Sarentino, Val Venosta, Passo Stelvio, Passo Pennes)
* 🇦🇹 **Carinzia - Austria** (8 siti: Emberger Alm, Nockalmstraße, Maltatal Kölnbreinsperre, Dobratsch)
* 🇸🇮 **Slovenia Occidentale** (8 siti: Mangartsko sedlo, Passo del Vršič, Pokljuka, Soriška Planina, Monte Krn)
* 🌊 **Costa & Lagune** (5 siti: Valle Vecchia / Brussa a Caorle, Delta del Po Sacca di Scardovari, Barricata, Foce Tagliamento)

---

## 🧭 Perché questo progetto?

Siti di riferimento come [LightPollutionMap.info](https://www.lightpollutionmap.info) offrono un eccellente strumento (*"Find closest dark site"*), ma il loro algoritmo calcola la distanza euclidea pura (**in linea d'aria**). 

In un territorio montuoso (Prealpi Carniche, Giulie, Bellunesi, Dolomiti e Alpi Giulie/Tauri), questo approccio risulta spesso fuorviante:
* **Inaccessibilità**: il punto indicato può cadere su una parete rocciosa impervia o in una gola senza strade.
* **Tempi di guida sproporzionati**: un punto a 30 km in linea d'aria può richiedere oltre 2h30m di auto per aggirare una catena montuosa.
* **Assenza di piazzali**: per astrofili e astrofotografi è indispensabile raggiungere il luogo con l'auto, poter parcheggiare in piano e avere un orizzonte aperto.

**Questo progetto risolve il problema:**
1. Interroga direttamente i raster fotometrici di **LightPollutionMap.info** (*modello Sky Brightness 2025* e *World Atlas 2015*).
2. Calcola con precisione **itinerari, distanze e tempi di guida reali** tramite motore **OSRM** (*Open Source Routing Machine*) in parallelo su multi-thread.
3. Fornisce un catalogo curato di oltre 80 valichi alpini, altopiani e passi con **accesso stradale verificato, quota e parcheggio**.
4. Dispone di una **Mappa Interattiva Leaflet**: cliccando su **qualsiasi punto** della mappa viene interrogato all'istante il database fotometrico e tracciato l'itinerario in auto con tempi e distanze.
5. Genera per ogni punto un pulsante per **avviare la navigazione direttamente con Google Maps**.

---

## 🏆 Eccellenze Astronomiche (SQM ≥ 21.70)

### 🇦🇹 Carinzia (Austria) — I cieli più bui d'Europa centrale
* **Nockalmstraße (Eisentalhöhe)** (2.049 m) — **SQM 21.90** • **3h 38m** (264 km) • Strada alpina d'alta quota, buio stellare eccezionale.
* **Emberger Alm (Drautal)** (1.800 m) — **SQM 21.88** • **3h 49m** (242 km) • Tempio internazionale degli astrofili (sede storica dell'ITT), orizzonte sud apertissimo.
* **Maltatal (Diga Kölnbreinsperre)** (1.933 m) — **SQM 21.93** • **3h 34m** (254 km) • Cuore degli Alti Tauri, orizzonte limpidissimo.

### 🇸🇮 Slovenia Occidentale — Gioielli del Parco Nazionale del Triglav
* **Passo del Vršič** (1.611 m) — **SQM 21.74** • **2h 36m** (215 km) • Tra Kranjska Gora e la Valle dell'Isonzo, cielo d'alta quota riparato.
* **Mangartsko sedlo** (2.055 m) — **SQM 21.73** • **2h 32m** (209 km) • La strada asfaltata più alta della Slovenia, orizzonte sud libero a 360°.
* **Altopiano di Pokljuka (Rudno Polje)** (1.345 m) — **SQM 21.74** • **3h 19m** (274 km) • Foreste di abeti del Triglav, totale assenza di luci urbane.

### 🇮🇹 Friuli-Venezia Giulia & Dolomiti
* **Casera Razzo / Passo Ciampigotto** (1.790 m) — **SQM 21.70** • **1h 45m** (123 km) • Regina dell'osservazione triveneta, piazzali vasti in piano e 360° di visuale.
* **Passo Pramollo (Nassfeld)** (1.530 m) — **SQM 21.76** • **2h 05m** (150 km) • SP110 comoda, buio notevole sulle Alpi Carniche orientali.
* **Passo Monte Croce Comelico** (1.636 m) — **SQM 21.72** • **1h 53m** (133 km) • SS52 veloce e aperta tutto l'anno.
* **Rifugio Auronzo (Tre Cime di Lavaredo)** (2.320 m) — **SQM 21.78** • **2h 15m** (145 km) • Strada a pedaggio sotto la parete sud delle Tre Cime.
* **Passo delle Erbe / Würzjoch (BZ)** (2.006 m) — **SQM 21.75** • **2h 55m** (188 km) • Sotto il Sass de Putia, tra i siti più rinomati dell'Alto Adige.
* **Passo Pennes / Penser Joch (BZ)** (2.211 m) — **SQM 21.78** • **3h 38m** (248 km) • Altissimo valico tra Sarentino e Vipiteno.

### 🌊 Costa & Lagune — Il mare buio a portata di mano
* **Delta del Po (Sacca di Scardovari)** (0 m) — **SQM 21.25** • **2h 29m** (150 km) • Orizzonte marino a sud completamente privo di lampioni a perdita d'occhio.
* **Valle Vecchia / Brussa (Caorle)** (0 m) — **SQM 20.91** • **1h 05m** (60 km) • L'oasi naturale costiera più buia dell'Alto Adriatico, raggiungibile in 1 ora da Ghirano!

---

## 🚀 Utilizzo in Locale

### Avvio rapido con file Batch (Windows)
* **`avvia_sqm_search.bat`**: avvia la dashboard Streamlit e apre automaticamente il browser all'indirizzo `http://localhost:8501`.
* **`apri_mappa.bat`**: apre direttamente a schermo intero la mappa interattiva Leaflet (`sqm_dark_sites_map.html`).

### Avvio manuale da terminale
```bash
# 1. Attiva l'ambiente virtuale
.venv\Scripts\activate

# 2. Avvia la dashboard
streamlit run app.py
```

---

## 📁 Struttura del Progetto

```
SqmSearch/
├── .venv/                      # Ambiente virtuale Python dedicato (escluso da Git)
├── .gitignore                  # File ignorati da Git
├── app.py                      # Applicazione web Streamlit interattiva con filtri per Area
├── sqm_analyzer.py             # Motore di calcolo concorrente: API LightPollutionMap + OSRM
├── sqm_dark_sites_map.html     # Mappa interattiva Leaflet (80+ siti, percorsi e click inspection)
├── requirements.txt            # Dipendenze Python (streamlit, pandas, requests)
├── avvia_sqm_search.bat        # Script di avvio per Windows (Streamlit)
├── apri_mappa.bat              # Script per aprire direttamente la mappa HTML
└── README.md                   # Documentazione del progetto
```

---

## 🛠️ Tecnologie & Fonti Dati

* **Python 3** con calcolo concorrente `ThreadPoolExecutor`
* **Streamlit** (Dashboard reattiva e responsive per desktop e smartphone)
* **Leaflet.js** (Mappe interattive con tile OpenStreetMap, Esri Topo ed Esri Imagery senza necessità di API key)
* **LightPollutionMap.info** (Dati di radianza e brillanza celeste zenithale)
* **OSRM Project** (Routing vettoriale e calcolo tempi di percorrenza stradale)
* **Falchi et al. (2016)** (Modello fotometrico per il calcolo della magnitudine limite e dell'SQM in mag/arcsec²)
