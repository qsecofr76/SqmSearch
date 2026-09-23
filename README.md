# 🌌 SQM Search & Driving Reachability Explorer

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://sqmsearch-eucsrbmdvsdt5tmgwfxg99.streamlit.app/)

Uno strumento interattivo open-source per individuare e valutare i **migliori siti di osservazione astronomica** incrociando la qualità del cielo buio (**SQM / Bortle**) con l'**effettiva raggiungibilità stradale in automobile** (tempi di guida e chilometri reali).

🚀 **Applicazione Web Online:** [https://sqmsearch-eucsrbmdvsdt5tmgwfxg99.streamlit.app/](https://sqmsearch-eucsrbmdvsdt5tmgwfxg99.streamlit.app/)  
Ottimizzata sia per l'uso da PC desktop che direttamente da smartphone sul campo.

> 🔭 *Applicazione sviluppata in omaggio al gruppo astrofili [**Astrofili Ponte di Piave**](https://www.astrofilipontedipiave.it/).*

---

## 🧭 Il Problema della Ricerca "In Linea d'Aria"

I portali astronomici tradizionali e i visualizzatori di inquinamento luminoso offrono solitamente una ricerca del sito buio più vicino basata sulla **distanza euclidea (linea d'aria)**. In contesti orografici complessi (Alpi, Prealpi e vallate), questo approccio presenta limiti critici:
* **Siti inaccessibili**: il punto teoricamente più buio può cadere su una parete rocciosa, su una vetta senza sentieri o in una forra priva di viabilità.
* **Tempi di viaggio ingannevoli**: una località a 25 km in linea d'aria può richiedere più di 2 ore di guida a causa della conformazione montuosa.
* **Assenza di spazi operativi**: per astrofili, astrofotografi e osservatori visuali è fondamentale raggiungere il sito direttamente in auto, disporre di piazzali in piano per montare montature e telescopi, ed evitare ostacoli visivi all'orizzonte.

**SQM Search risolve il problema alla radice**, combinando i modelli fotometrici satellitari con il calcolo dei percorsi stradali reali.

---

## ✨ Funzionalità Principali

* 🏢 **Profili Territoriali Preimpostati**:
  * **Triveneto (Default)**: Partenza predefinita `Ghirano di Prata (PN)` e catalogo dedicato di 85 siti tra FVG, Veneto, Trentino-Alto Adige, Carinzia e Slovenia.
  * **Lombardia Nord**: Partenza predefinita `Como (CO)` e catalogo dedicato di 69 siti tra Comasco, Lecco, Valsassina, Varesotto, Valtellina/Sondrio, Canton Ticino (CH), Verbano e Val d'Ossola.
* 📍 **Punto di Partenza Personalizzabile**:
  * Caricamento istantaneo precalcolato a 0.0s all'avvio.
  * Ricerca potenziata multi-sorgente per nome: riconosce passi montani storici, rifugi, vette, comuni, coordinate GPS o link Google Maps.
  * Inserimento manuale rapido di latitudine e longitudine GPS.
* 🚗 **Routing Stradale Reale con OSRM**:
  * Calcolo istantaneo di tempi di percorrenza e distanze chilometriche effettive su strada.
  * Navigazione assistita: clic diretto sul nome della località per aprire l'itinerario in **Google Maps** e avviare il navigatore.
* 🌌 **Analisi Fotometrica e Qualità del Cielo**:
  * Interrogazione dei raster di *LightPollutionMap.info* (*Sky Brightness 2025* e *World Atlas 2015*).
  * Valore **SQM** (Sky Quality Meter in mag/arcsec²), stima della **Classe Bortle**, **NELM** (Naked Eye Limiting Magnitude) e quota sul livello del mare.
* 🗺️ **Mappa Interattiva Leaflet Dinamica**:
  * Mappa generata al volo e centrata sul profilo attivo.
  * Cliccando su **qualsiasi punto della mappa** viene interrogato all'istante il database fotometrico e tracciato l'itinerario in tempo reale dal punto di partenza selezionato.
  * Selettore di layer cartografici: **Stradale (OpenStreetMap)**, **Rilievo Montano (Esri Topo)** e **Satellite (Esri Imagery)**.
* 📋 **Classifica Ordinata per Tempo di Guida**:
  * Visualizzazione immediata di tutti i siti del catalogo ordinati dal più vicino al più lontano in auto.
  * Righe colorate ad alto contrasto in base alla qualità del cielo (SQM).
* 🔍 **Modalità Test Libero**:
  * Possibilità di testare qualsiasi coordinata o toponimo per verificarne istantaneamente SQM e itinerario stradale.

---

## 🗺️ Aree & Cataloghi Inclusi

Il database include oltre **150 siti osservativi verificati con accesso veicolare e piazzali**, suddivisi nei cataloghi:

### 1. Catalogo Triveneto (85 siti)
* 🇮🇹 **Friuli-Venezia Giulia**: Carnia, Tarvisiano, Sella Nevea, Alpi e Prealpi Giulie, Meduno Startplatz, Dolomiti Friulane.
* 🇮🇹 **Veneto**: Dolomiti Bellunesi, Monte Pizzoc/Cansiglio, Monte Avena, Cadore, Altopiano di Asiago, Monte Grappa, Lessinia.
* 🇮🇹 **Trentino-Alto Adige**: Val Badia, Val di Fassa, Val Sarentino, Val Venosta, passi dolomitici d'alta quota.
* 🇦🇹 **Carinzia (Austria)**: Alti Tauri, Nockberge, Sonnleitn/Nassfeld, Emberger Alm, Maltatal, Weissensee.
* 🇸🇮 **Slovenia Occidentale**: Parco Nazionale del Triglav, Mangartsko sedlo, Passo del Vršič, Altopiano di Pokljuka.
* 🌊 **Costa Adriatica**: Valle Vecchia / Brussa, Sacca di Scardovari nel Delta del Po.

### 2. Catalogo Lombardia Nord (69 siti)
* 🇮🇹 **Comasco, Triangolo Lariano & Bellagio**: Colma di Sormano, Pian del Tivano, Monte San Primo, Sighignola (Balcone d'Italia), Rifugio Venini, Pigra, Alpe del Vicerè.
* 🇮🇹 **Lecco, Valsassina & Grigne**: Alpe Giumello, Cainallo, Piani dei Resinelli, Culmine di San Pietro, Rifugio Roccoli Lorla (Colico), Piani di Bobbio.
* 🇮🇹 **Varesotto & Verbano Orientale**: Campo dei Fiori (Schiaparelli), Passo Forcora, Passo del Cuvignone, Monte San Martino, Monte Sette Termini.
* 🇮🇹 **Sondrio, Valtellina & Valchiavenna**: Passo San Marco, Predarossa, Val di Mello, Chiareggio, Campo Moro, Passo dello Spluga, Montespluga, Mortirolo, Foscagno, Cancano, Passo Gavia, Bernina.
* 🇨🇭 **Canton Ticino**: Monte Lema, Passo San Gottardo, Passo San Bernardino, Lucomagno, Passo della Novena (Nufenenpass), Alpe di Neggia, Val Verzasca, Val Bavona.
* 🇮🇹 **Arona, Verbano Occidentale, Cusio & Val d'Ossola**: Mottarone, Alpe Devero, Val Formazza (Riale), Passo del Sempione, Macugnaga, Alpe Colle (Val Grande).

---

## 🚀 Utilizzo

### 📱 Online su Streamlit Cloud (Nessuna installazione richiesta)
L'applicazione è attiva e fruibile direttamente da browser:

👉 **[Apri SQM Search su Streamlit Cloud](https://sqmsearch-eucsrbmdvsdt5tmgwfxg99.streamlit.app/)**

### 💻 Esecuzione in Locale
```bash
# 1. Clona il repository
git clone https://github.com/qsecofr76/SqmSearch.git
cd SqmSearch

# 2. Crea e attiva l'ambiente virtuale
python -m venv .venv
# Su Windows:
.venv\Scripts\activate
# Su Linux/macOS:
source .venv/bin/activate

# 3. Installa le dipendenze
pip install -r requirements.txt

# 4. Avvia l'applicazione
streamlit run app.py
```

---

## 📁 Struttura del Progetto

```
SqmSearch/
├── app.py                      # Applicazione web interattiva Streamlit (Profili, Classifica, Mappa)
├── sqm_analyzer.py             # Motore di calcolo: API LPM, OSRM Table Service, Profili Territoriali
├── catalogs/                   # Cataloghi astronomici JSON
│   ├── nordest.json            # 85 siti Triveneto, Carinzia, Slovenia
│   └── lombardia_nord.json     # 69 siti Comasco, Lecco, Varesotto, Valtellina, Ticino, Verbano
├── assets/                     # Loghi e risorse grafiche (Astrofili Ponte di Piave)
├── sqm_dark_sites_map.html     # Mappa interattiva Leaflet esportabile
├── requirements.txt            # Dipendenze Python (streamlit, pandas, requests)
├── avvia_sqm_search.bat        # Script di avvio rapido locale (Windows)
├── apri_mappa.bat              # Script per apertura diretta della mappa nel browser
└── README.md                   # Documentazione del progetto
```

---

## 🛠️ Tecnologie Utilizzate

* **Python 3** con calcolo batch ultra-veloce (`OSRM Table Service`).
* **Streamlit** per l'interfaccia utente web reattiva e compatibile con dispositivi mobili.
* **Leaflet.js** per la cartografia interattiva e il calcolo dinamico al click.
* **OSRM (Open Source Routing Machine)** per il calcolo stradale e le geometrie dei percorsi.
* **LightPollutionMap.info API** per i dati di brillanza zenitale del cielo (modello Falchi et al. / VIIRS).
* **OpenStreetMap & Open-Meteo Geocoding** per la risoluzione dei toponimi in coordinate geografiche.
