# 🌌 SQM Search & Driving Reachability Tool

Uno strumento per individuare e valutare i **migliori siti di osservazione astronomica** (con qualità del cielo buio **SQM > 21.7** o personalizzabile) superando il limite della ricerca "in linea d'aria" di *LightPollutionMap*, integrando i **tempi di percorrenza e le distanze stradali reali in auto**.

Punto di partenza predefinito: **Ghirano di Prata (PN)** *(modificabile liberamente dall'app)*.

---

## 🧭 Perché questo progetto?

Siti di riferimento come [LightPollutionMap.info](https://www.lightpollutionmap.info) offrono un eccellente strumento (*"Find closest dark site"*), ma il loro algoritmo calcola la distanza euclidea pura (**in linea d'aria**). 

In un territorio montuoso (Prealpi Carniche, Giulie, Bellunesi e Dolomiti), questo approccio risulta spesso fuorviante:
* **Inaccessibilità**: il punto indicato può cadere su una parete rocciosa impervia o in una gola senza strade.
* **Tempi di guida sproporzionati**: un punto a 30 km in linea d'aria può richiedere oltre 2h30m di auto per aggirare una catena montuosa.
* **Assenza di piazzali**: per astrofili e astrofotografi è indispensabile raggiungere il luogo con l'auto, poter parcheggiare in piano e avere un orizzonte aperto.

**Questo progetto risolve il problema:**
1. Interroga direttamente i raster fotometrici di **LightPollutionMap.info** (*modello Sky Brightness 2025* e *World Atlas 2015*).
2. Calcola con precisione **itinerari, distanze e tempi di guida reali** tramite motore **OSRM** (*Open Source Routing Machine*).
3. Fornisce un catalogo curato di valichi alpini, altopiani e passi con **accesso stradale verificato e parcheggio**.
4. Genera per ogni punto un pulsante per **avviare la navigazione direttamente con Google Maps**.

---

## 🏆 I Migliori Siti Astronomici (SQM ≥ 21.70 da Ghirano)

| # | Località | SQM 2025 | Bortle | Quota | Distanza Auto | Tempo Guida | Caratteristiche & Accesso |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| **1** | **Casera Razzo / Passo Ciampigotto** | **21.70** | 3 | 1.857 m | 123 km | **1h 45m** | **Scelta regina:** SP619 asfaltata. Enormi piazzali in piano (Rif. Fabbro / Malga Razzo). Orizzonte a 360°, quota sopra le inversioni termiche. Storico Star Party Triveneto. |
| **2** | **Val Visdende (Pradon del Ghelp)** | **21.70** | 3 | 1.339 m | 127 km | **1h 51m** | Asfalto da San Pietro di Cadore. Valle alpina isolata con zero luci locali, protetta da pareti rocciose. |
| **3** | **Passo Monte Croce Comelico** | **21.80** | 3 / 2 | 1.644 m | 133 km | **1h 53m** | SS52 Carnica veloce e aperta tutto l'anno. Cielo est e nord scurissimo al confine con l'Alto Adige. Ampi parcheggi. |
| **4** | **Pradibosco / Pian di Casa (Val Pesarina)** | **21.72** | 3 | 1.707 m | 134 km | **1h 57m** | SR465 della Val Pesarina verso Forcella Lavardet. Centro fondo / Pian di Casa. Valle silenziosa senza traffico notturno. |
| **5** | **Passo Valparola (Forte Tre Sassi)** | **21.71** | 3 | 2.169 m | 141 km | **1h 59m** | A monte del Falzarego (SP24). Grandissimo piazzale asfaltato presso il Forte Tre Sassi a quasi 2.200m. Aria purissima e trasparenza al top. |
| **6** | **Lago d'Antorno (Misurina)** | **21.76** | 3 | 1.850 m | 139 km | **2h 00m** | SP49, 1.5 km dopo Misurina verso le Tre Cime. Grande piazzale al lago. Schermato da luci dirette, ottima visibilità zenitale. |
| **7** | **Passo Tre Croci** | **21.74** | 3 | 1.772 m | 138 km | **2h 05m** | SR48 delle Dolomiti tra Auronzo e Cortina. Parcheggi e piazzole al valico. |
| **8** | **Rifugio Auronzo (Tre Cime di Lavaredo)** | **21.78** | 3 / 2 | 2.323 m | 145 km | **2h 15m** | Strada a pedaggio estiva/autunnale. Piazzali a 2.320m sotto la parete sud. Il cielo più buio d'alta quota raggiungibile direttamente in auto. |
| **9** | **Altopiano del Montasio (Malga Montasio)** | **21.70** | 3 | 1.576 m | 123 km | **2h 16m** | Da Chiusaforte/Sella Nevea. Parcheggio all'altopiano. Orizzonte sud libero verso le Giulie, protetto a nord dalla parete del Montasio. |
| **10** | **Passo Monte Croce Carnico (Plöckenpass)** | **21.78** | 3 | 1.379 m | 174 km | **2h 18m** | SS52bis ampia da Tolmezzo/Paluzza fino al valico di confine. Grande piazzale con vista aperta a nord. |

### ⚡ I "Compromessi Veloci" (SQM 21.55 – 21.68, tempi guida 1h15m – 1h35m)
Ideali per sessioni rapide o infrasettimanali:
* **Passo Cibiana** (1.569 m) — **SQM 21.58** • **1h 24m** (100 km).
* **Passo Duran** (1.610 m) — **SQM 21.56** • **1h 27m** (102 km).
* **Passo Staulanza** (1.766 m) — **SQM 21.62** • **1h 32m** (106 km).
* **Passo Giau** (2.236 m) — **SQM 21.65** • **1h 55m** (126 km, quota altissima).

---

## 🚀 Utilizzo in Locale

Il progetto è preconfigurato con un ambiente virtuale dedicato.

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

## 🌐 Pubblicazione Online (per vederla su Cellulare)

### Opzione A: Pubblicazione su Streamlit Community Cloud (Consigliata)
Permette di usare l'app completa su smartphone con slider, calcolo punti e filtri:

1. Crea un nuovo repository sul tuo profilo [GitHub](https://github.com/new) (es. `SqmSearch`).
2. Esegui questi comandi nella cartella del progetto:
   ```bash
   git init
   git add .
   git commit -m "Primo commit SQM Search"
   git branch -M main
   git remote add origin https://github.com/TUO-USERNAME/SqmSearch.git
   git push -u origin main
   ```
3. Vai su [share.streamlit.io](https://share.streamlit.io) e accedi con GitHub.
4. Clicca su **"New app"**, seleziona il repository `SqmSearch` e come Main file path indica `app.py`.
5. Clicca su **"Deploy"**: in 2 minuti otterrai un link pubblico (es. `https://sqmsearch.streamlit.app`) condivisibile con chiunque via smartphone.

### Opzione B: Pubblicazione su GitHub Pages (Solo Mappa)
Se vuoi pubblicare soltanto la mappa interattiva autonoma:
1. Rinomina `sqm_dark_sites_map.html` in `index.html`.
2. Carica il repository su GitHub.
3. Vai in **Settings** $\rightarrow$ **Pages**, seleziona il branch `main` e la cartella `/ (root)` e clicca **Save**.
4. Avrai un link statico del tipo `https://tuo-username.github.io/SqmSearch/`.

---

## 📁 Struttura del Progetto

```
SqmSearch/
├── .venv/                      # Ambiente virtuale Python dedicato (escluso da Git)
├── .gitignore                  # File ignorati da Git
├── app.py                      # Applicazione web Streamlit interattiva
├── sqm_analyzer.py             # Motore di calcolo: API LightPollutionMap + OSRM
├── sqm_dark_sites_map.html     # Mappa interattiva Leaflet (OSM, Topo, Satellite)
├── requirements.txt            # Dipendenze Python (streamlit, pandas, requests)
├── avvia_sqm_search.bat        # Script di avvio per Windows (Streamlit)
├── apri_mappa.bat              # Script per aprire direttamente la mappa HTML
└── README.md                   # Documentazione del progetto
```

---

## 🛠️ Tecnologie & Fonti Dati

* **Python 3**
* **Streamlit** (Dashboard reattiva e responsive per desktop e smartphone)
* **Leaflet.js** (Mappe interattive con tile OpenStreetMap ed Esri Topo/Imagery senza bisogno di API key)
* **LightPollutionMap.info** (Dati di radianza e brillanza celeste zenithale)
* **OSRM Project** (Routing vettoriale e calcolo tempi di percorrenza stradale)
* **Falchi et al. (2016)** (Modello fotometrico per il calcolo della magnitudine limite e dell'SQM in mag/arcsec²)
