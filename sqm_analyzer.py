"""
SQM Search & Driving Reachability Tool
Analisi siti con elevato SQM (> 20.0) e calcolo tempo reale di percorrenza in auto da Ghirano di Prata (PN).
Dati SQM interrogati direttamente dai server di LightPollutionMap.info (modelli SB 2025 e World Atlas 2015).
Distanze e tempi di guida calcolati tramite motore OSRM (Open Source Routing Machine).
Copertura estesa: Triveneto (Friuli-Venezia Giulia, Veneto, Trentino-Alto Adige), Carinzia (Austria), Slovenia Occidentale e Costa Adriatica / Delta del Po.
"""

import base64
import time
import math
import json
import requests
import concurrent.futures
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple

# Coordinate di partenza predefinite: Ghirano di Prata di Pordenone (PN)
DEFAULT_ORIGIN = {
    "name": "Ghirano di Prata (PN)",
    "lat": 45.8617,
    "lon": 12.5539
}

# Catalogo completo di siti di osservazione con accesso stradale verificato
# Copre Triveneto, Carinzia, Slovenia Occidentale e Costa & Lagune
CURATED_SITES = [
    # ==========================================
    # FRIULI-VENEZIA GIULIA (21 SITI)
    # ==========================================
    {
        "name": "Casera Razzo / Passo Ciampigotto",
        "lat": 46.4795,
        "lon": 12.5855,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Cadore / Carnia (BL/UD)",
        "access": "Strada provinciale SP619 asfaltata. Ampio piazzale/parcheggio in piano (Rif. Tenente Fabbro / Malga Razzo). Sito storico Star Party Astrofili Triveneti a 1790m. Orizzonte aperto a 360°, quota elevatissima sopra inversioni termiche.",
        "paved": True
    },
    {
        "name": "Passo Pramollo (Nassfeld)",
        "lat": 46.5644,
        "lon": 13.2756,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Pontebba / Confine Carinzia (UD/A)",
        "access": "SP110 comoda da Pontebba. Valico alpino a 1530m con ampi parcheggi all'ex confine. Buio notevole sulle Alpi Carniche orientali. SQM ~21.76.",
        "paved": True
    },
    {
        "name": "Passo Monte Croce Carnico (Plöckenpass)",
        "lat": 46.6033,
        "lon": 12.9444,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Paluzza / Confine Austria (UD)",
        "access": "SS52bis comoda e asfaltata. Ampio parcheggio all'ex valico di confine a 1360m. Buio notevole verso nord e cielo montano molto limpido.",
        "paved": True
    },
    {
        "name": "Rifugio Tolazzi (Forni Avoltri / Collina)",
        "lat": 46.5911,
        "lon": 12.8358,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Forni Avoltri / Alpi Carniche (UD)",
        "access": "Strada comunale asfaltata da Rigolato/Collina. Grande parcheggio terminale a 1350m ai piedi del Monte Coglians. Valle chiusa senza inquinamento luminoso.",
        "paved": True
    },
    {
        "name": "Pradibosco / Pian di Casa (Val Pesarina)",
        "lat": 46.5167,
        "lon": 12.6667,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Prato Carnico / Val Pesarina (UD)",
        "access": "SR465 della Val Pesarina. Parcheggi presso Pian di Casa e centro fondo a 1235m. Valle appartata e tranquilla senza traffico notturno.",
        "paved": True
    },
    {
        "name": "Sauris di Sopra (Sella Festons)",
        "lat": 46.4750,
        "lon": 12.6833,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Sauris / Alta Carnia (UD)",
        "access": "Strada panoramica asfaltata da Sauris di Sopra verso Sella Festons a 1730m. Buio di alta montagna nel cuore della Carnia.",
        "paved": True
    },
    {
        "name": "Passo Pura (Lago di Sauris)",
        "lat": 46.4428,
        "lon": 12.7844,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Ampezzo / Sauris (UD)",
        "access": "SP73 asfaltata con tornanti nel bosco. Parcheggio al valico a 1425m con vista verso la conca di Ampezzo e il Tagliamento.",
        "paved": True
    },
    {
        "name": "Altopiano del Montasio (Malga Montasio)",
        "lat": 46.4161,
        "lon": 13.4219,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Chiusaforte / Sella Nevea (UD)",
        "access": "Strada asfaltata panoramica che sale da Sella Nevea fino al parcheggio della Malga Montasio a 1520m. Orizzonte sud completamente aperto verso le Alpi Giulie, protetto a nord dal massiccio del Montasio.",
        "paved": True
    },
    {
        "name": "Sella Nevea (Piazzale Rif. Gilberti)",
        "lat": 46.3889,
        "lon": 13.4806,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Chiusaforte (UD)",
        "access": "SP76 asfaltata. Ampi piazzali di sosta a 1210m tra il Montasio e il massiccio del Canin. Buio notevole e orizzonte aperto verso est.",
        "paved": True
    },
    {
        "name": "Laghi di Fusine (Lago Superiore)",
        "lat": 46.4789,
        "lon": 13.6708,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Tarvisio / Fusine (UD)",
        "access": "Strada asfaltata da Fusine in Valromana fino al parcheggio del Lago Superiore a 956m. Orizzonte sud verso l'imponente parete nord del Mangart, luogo suggestivo e protetto.",
        "paved": True
    },
    {
        "name": "Val Saisera (Malga Saisera)",
        "lat": 46.4833,
        "lon": 13.4833,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Malborghetto-Valbruna / Alpi Giulie (UD)",
        "access": "Strada asfaltata lungo la Val Saisera fino ai parcheggi terminali sotto il Jôf Fuart e Jôf di Montasio a 990m. Molto riparata dalle luci urbane.",
        "paved": True
    },
    {
        "name": "Monte Zoncolan (Piazzale Vetta)",
        "lat": 46.5014,
        "lon": 12.9286,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Sutrio / Ovaro (UD)",
        "access": "Strada asfaltata da Sutrio o da Ovaro. Grande piazzale al valico a 1730m. Panorama a 360° sulla Carnia, sopra le inversioni termiche.",
        "paved": True
    },
    {
        "name": "Passo Rest",
        "lat": 46.3533,
        "lon": 12.8392,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Tramonti di Sopra / Priuso (PN/UD)",
        "access": "SP552 asfaltata ma con tornanti. Piazzole al valico a 1052m. Valle selvaggia e isolata tra Tagliamento e Val Tramontina.",
        "paved": True
    },
    {
        "name": "Sella Carnizza (Val Resia)",
        "lat": 46.3458,
        "lon": 13.3167,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Resia / Lusevera (UD)",
        "access": "SP42 asfaltata. Valico a 1086m tra Val Resia e Alta Val Torre. Zona silenziosa e schermata dalle luci di pianura e fondovalle.",
        "paved": True
    },
    {
        "name": "Passo Tanamea (Alta Val Torre)",
        "lat": 46.3014,
        "lon": 13.3642,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Lusevera / Val Musi (UD)",
        "access": "SR646 verso Uccea e il confine sloveno. Piazzola al valico a 851m nel Parco Prealpi Giulie, incastonata tra i Musi e il Gran Monte.",
        "paved": True
    },
    {
        "name": "Matajur / Rifugio Pelizzo",
        "lat": 46.2058,
        "lon": 13.5414,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Savogna / Valli del Natisone (UD)",
        "access": "Strada asfaltata panoramica che sale fino al piazzale del Rifugio Pelizzo a 1320m. Orizzonte aperto a 180° verso sud ed est.",
        "paved": True
    },
    {
        "name": "Sella Chianzutan",
        "lat": 46.3750,
        "lon": 12.9667,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Verzegnis / Val d'Arzino (UD)",
        "access": "SP1 comoda e asfaltata tra Tolmezzo e la Val d'Arzino. Piazzale al valico a 955m. Raggiungibile in ~1h 38m da Ghirano.",
        "paved": True
    },
    {
        "name": "Pala Barzana",
        "lat": 46.2333,
        "lon": 12.7333,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Andreis / Poffabro (PN)",
        "access": "SP26 della Pala Barzana. Valico a 840m tra Valcellina e Val Colvera. Zona appartata a circa 1h da Ghirano.",
        "paved": True
    },
    {
        "name": "Passo Sant'Osvaldo (Erto)",
        "lat": 46.2750,
        "lon": 12.3833,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Erto e Casso / Vajont (PN)",
        "access": "SR251 comoda attraverso la Valcellina. Piazzali a Erto e presso la diga del Vajont a 827m. Raggiungibile in ~1h 09m da Ghirano.",
        "paved": True
    },
    {
        "name": "Piancavallo (Castaldia)",
        "lat": 46.1083,
        "lon": 12.5083,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Aviano (PN)",
        "access": "SP31 veloce da Aviano. Parcheggio dorsale Castaldia a 1470m. Raggiungibile in soli ~56m da Ghirano! Buono verso nord, disturbo della pianura verso sud.",
        "paved": True
    },
    {
        "name": "Val Cimoliana (Pian Meluzzo / Rif. Pordenone)",
        "lat": 46.3888,
        "lon": 12.5135,
        "macro_region": "Friuli-Venezia Giulia",
        "region": "Cimolais / Parco Dolomiti Friulane (PN)",
        "access": "Val Cimoliana dal centro di Cimolais: strada asfaltata nel primo tratto poi sterrata/ghiaiosa fino a Pian Meluzzo a 1163m. Luogo selvaggio nel cuore del Parco. Attenzione al fondo stradale ghiaioso nell'ultimo tratto.",
        "paved": False
    },

    # ==========================================
    # VENETO (25 SITI)
    # ==========================================
    {
        "name": "Passo Valparola (Forte Tre Sassi)",
        "lat": 46.5278,
        "lon": 11.9902,
        "macro_region": "Veneto",
        "region": "Livinallongo / Badia (BL/BZ)",
        "access": "SP24 del Passo Valparola (accanto al Passo Falzarego). Enorme piazzale asfaltato presso il Forte Tre Sassi a quasi 2200m di quota. Trasparenza eccellente, sopra lo strato limite atmosferico.",
        "paved": True
    },
    {
        "name": "Rifugio Auronzo (Tre Cime di Lavaredo)",
        "lat": 46.6124,
        "lon": 12.2952,
        "macro_region": "Veneto",
        "region": "Auronzo di Cadore (BL)",
        "access": "Strada panoramica a pedaggio (stagionale). Grandi piazzali asfaltati a 2320m sotto la parete sud delle Tre Cime. Buio d'alta quota e seeing eccezionale.",
        "paved": True
    },
    {
        "name": "Passo Monte Croce Comelico",
        "lat": 46.6561,
        "lon": 12.4208,
        "macro_region": "Veneto",
        "region": "Comelico Superiore / Sesto (BL/BZ)",
        "access": "Strada Statale SS52 Carnica, molto ampia e sempre aperta. Diversi parcheggi lungo il valico a 1636m. Cielo nord ed est scurissimo al confine con l'Alto Adige.",
        "paved": True
    },
    {
        "name": "Val Visdende (Pradon del Ghelp)",
        "lat": 46.5667,
        "lon": 12.6500,
        "macro_region": "Veneto",
        "region": "San Pietro di Cadore (BL)",
        "access": "Strada asfaltata da San Pietro di Cadore. Ampie radure e parcheggi a 1300m. Valle alpina isolata, zero inquinamento luminoso locale, protetta da alte pareti rocciose.",
        "paved": True
    },
    {
        "name": "Lago d'Antorno (Misurina)",
        "lat": 46.5942,
        "lon": 12.2597,
        "macro_region": "Veneto",
        "region": "Auronzo / Misurina (BL)",
        "access": "SP49 circa 1.5 km a nord del Lago di Misurina. Ampio piazzale a 1866m in riva al laghetto prima del casello per le Tre Cime. Schermato da luci dirette, cielo zenitale limpidissimo.",
        "paved": True
    },
    {
        "name": "Passo Falzarego",
        "lat": 46.5186,
        "lon": 12.0089,
        "macro_region": "Veneto",
        "region": "Cortina d'Ampezzo / Livinallongo (BL)",
        "access": "SR48 delle Dolomiti. Ampio piazzale al valico a 2105m sotto il Sass de Stria e il Lagazuoi. Trasparenza eccellente.",
        "paved": True
    },
    {
        "name": "Passo Giau",
        "lat": 46.4825,
        "lon": 12.0538,
        "macro_region": "Veneto",
        "region": "Colle Santa Lucia / Cortina (BL)",
        "access": "SP638 panoramica asfaltata. Grandi piazzali a 2236m. Orizzonte a 360°, aria finissima, SQM ~21.65.",
        "paved": True
    },
    {
        "name": "Passo Tre Croci",
        "lat": 46.5819,
        "lon": 12.2558,
        "macro_region": "Veneto",
        "region": "Cortina d'Ampezzo / Auronzo (BL)",
        "access": "SR48 delle Dolomiti. Piazzole e parcheggi al valico a 1805m tra il Cristallo e il Sorapis.",
        "paved": True
    },
    {
        "name": "Passo Cibiana",
        "lat": 46.3756,
        "lon": 12.2583,
        "macro_region": "Veneto",
        "region": "Valle di Cadore / Forno di Zoldo (BL)",
        "access": "SP347 del Passo Cibiana asfaltata. Parcheggi presso il valico a 1530m (Rifugio Remauro). Raggiungibile in soli ~1h 24m da Ghirano!",
        "paved": True
    },
    {
        "name": "Passo Duran",
        "lat": 46.3253,
        "lon": 12.0945,
        "macro_region": "Veneto",
        "region": "Val di Zoldo / Agordo (BL)",
        "access": "SP347 asfaltata tra Zoldo e Agordo. Piazzale presso Rifugio San Sebastiano a 1601m. Raggiungibile in ~1h 27m, buio notevole tra Civetta e San Sebastiano.",
        "paved": True
    },
    {
        "name": "Passo Staulanza",
        "lat": 46.4215,
        "lon": 12.1039,
        "macro_region": "Veneto",
        "region": "Val di Zoldo / Selva di Cadore (BL)",
        "access": "SP251 asfaltata. Piazzale al valico tra Pelmo e Civetta a 1766m. Raggiungibile in ~1h 32m da Ghirano.",
        "paved": True
    },
    {
        "name": "Passo Mauria",
        "lat": 46.4608,
        "lon": 12.5292,
        "macro_region": "Veneto",
        "region": "Lorenzago di Cadore / Forni di Sopra (BL/UD)",
        "access": "SS52 comoda e ampia. Parcheggi al valico a 1298m. SQM ~21.67 in ~1h 48m da Ghirano.",
        "paved": True
    },
    {
        "name": "Passo Fedaia (Diga / Marmolada)",
        "lat": 46.4567,
        "lon": 11.8864,
        "macro_region": "Veneto",
        "region": "Rocca Pietore / Canazei (BL/TN)",
        "access": "SP641 asfaltata. Grandi piazzali lungo il lago e la diga ai piedi della Marmolada a 2057m. Buio eccellente.",
        "paved": True
    },
    {
        "name": "Passo San Pellegrino",
        "lat": 46.3778,
        "lon": 11.7892,
        "macro_region": "Veneto",
        "region": "Falcade / Moena (BL/TN)",
        "access": "SS346 comoda e ampia. Grandi parcheggi al valico a 1918m tra Veneto e Trentino.",
        "paved": True
    },
    {
        "name": "Passo Valles",
        "lat": 46.3392,
        "lon": 11.7828,
        "macro_region": "Veneto",
        "region": "Falcade / Paneveggio (BL/TN)",
        "access": "SP81 asfaltata. Piazzale al valico a 2032m sotto le Pale di San Martino.",
        "paved": True
    },
    {
        "name": "Altopiano di Asiago (Campomulo / Centro Fondo)",
        "lat": 45.9392,
        "lon": 11.5647,
        "macro_region": "Veneto",
        "region": "Gallio / Altopiano dei Sette Comuni (VI)",
        "access": "Strada asfaltata da Gallio fino al Centro Fondo Campomulo a 1530m. Ampio pianoro a nord dell'Altopiano, schermato dai centri abitati.",
        "paved": True
    },
    {
        "name": "Altopiano di Asiago (Cima Larici / Val Formica)",
        "lat": 45.9472,
        "lon": 11.4428,
        "macro_region": "Veneto",
        "region": "Camporovere / Roana (VI)",
        "access": "Strada asfaltata verso il Rifugio Larici da Val d'Assa. Grande piazzale a 1650m aperto verso la Valsugana e Cima Portule.",
        "paved": True
    },
    {
        "name": "Passo Brocon",
        "lat": 46.1183,
        "lon": 11.6917,
        "macro_region": "Veneto",
        "region": "Castello Tesino / Canal San Bovo (BL/TN)",
        "access": "SP79 / SP169 asfaltata. Ampio parcheggio al valico a 1616m con orizzonte aperto sul Lagorai e le Pale di San Martino.",
        "paved": True
    },
    {
        "name": "Val Canzoi (Lago della Stua)",
        "lat": 46.1550,
        "lon": 11.9750,
        "macro_region": "Veneto",
        "region": "Cesiomaggiore / Dolomiti Bellunesi (BL)",
        "access": "Strada asfaltata fino al parcheggio della Val Canzoi (Parco Nazionale Dolomiti Bellunesi) a 700m. Valle stretta e riparata dalle luci.",
        "paved": True
    },
    {
        "name": "Cansiglio (Pian Osteria / Campo di Mezzo)",
        "lat": 46.0694,
        "lon": 12.4042,
        "macro_region": "Veneto",
        "region": "Alpago / Tambre (BL)",
        "access": "SP422 veloce da Caneva o Vittorio Veneto. Ampio pianoro dell'altopiano del Cansiglio a 1000m, parcheggi in piano. Raggiungibile in soli ~50m da Ghirano! SQM ~21.04.",
        "paved": True
    },
    {
        "name": "Alpe del Nevegal (Piazzale)",
        "lat": 46.0917,
        "lon": 12.2833,
        "macro_region": "Veneto",
        "region": "Belluno (BL)",
        "access": "SP31 comoda da Belluno/Cadola. Grandi piazzali asfaltati a 1080m con vista aperta a nord sulle Dolomiti Bellunesi. Raggiungibile in ~1h 02m.",
        "paved": True
    },
    {
        "name": "Monte Cesen (Malga Mariech)",
        "lat": 45.9292,
        "lon": 12.0167,
        "macro_region": "Veneto",
        "region": "Valdobbiadene (TV)",
        "access": "Strada panoramica asfaltata fino alla sommità del Monte Cesen / Malga Mariech a 1500m. Grande piazzale con orizzonte aperto. Raggiungibile in ~1h 15m.",
        "paved": True
    },
    {
        "name": "Cima Grappa (Rifugio Bassano)",
        "lat": 45.8722,
        "lon": 11.8028,
        "macro_region": "Veneto",
        "region": "Monte Grappa (TV/VI/BL)",
        "access": "SP140 Strada Cadorna. Vasto piazzale asfaltato a quasi 1800m. Quota elevata sopra le nebbie della pianura. Raggiungibile in ~1h 30m.",
        "paved": True
    },
    {
        "name": "Lessinia (Bocca di Selva / San Giorgio)",
        "lat": 45.6567,
        "lon": 11.0544,
        "macro_region": "Veneto",
        "region": "Bosco Chiesanuova / Parco della Lessinia (VR)",
        "access": "SP13 e SP253 fino a Bocca di Selva a 1550m. Grande altipiano carsico con ampi pascoli aperti verso nord e le Dolomiti di Brenta.",
        "paved": True
    },
    {
        "name": "Passo San Boldo",
        "lat": 46.0078,
        "lon": 12.1706,
        "macro_region": "Veneto",
        "region": "Cison di Valmarino / Trichiana (TV/BL)",
        "access": "SP635 dei 100 giorni. Parcheggi al valico a 706m. Raggiungibile in soli ~55m da Ghirano.",
        "paved": True
    },

    # ==========================================
    # TRENTINO-ALTO ADIGE (14 SITI)
    # ==========================================
    {
        "name": "Passo delle Erbe (Würzjoch)",
        "lat": 46.6744,
        "lon": 11.8133,
        "macro_region": "Trentino-Alto Adige",
        "region": "San Martino in Badia / Funes (BZ)",
        "access": "SP29 panoramica asfaltata. Grande parcheggio al valico a 2006m sotto la parete nord del Sass de Putia. Noto e apprezzatissimo punto di osservazione astronomica dolomitico. SQM ~21.75.",
        "paved": True
    },
    {
        "name": "Passo Pennes (Penser Joch)",
        "lat": 46.8178,
        "lon": 11.4406,
        "macro_region": "Trentino-Alto Adige",
        "region": "Sarentino / Vipiteno (BZ)",
        "access": "SS508 panoramica asfaltata. Valico ad alta quota a 2211m tra Val Sarentino e Wipptal. Vasto parcheggio al rifugio di vetta. Buio profondo eccezionale: SQM ~21.78.",
        "paved": True
    },
    {
        "name": "Passo Giovo (Jaufenpass)",
        "lat": 46.8272,
        "lon": 11.3208,
        "macro_region": "Trentino-Alto Adige",
        "region": "San Leonardo in Passiria / Vipiteno (BZ)",
        "access": "SS44 asfaltata. Valico alpino a 2094m tra la Passiria e la Val d'Isarco. Parcheggi al passo con vista sulle Alpi Breonie. SQM ~21.72.",
        "paved": True
    },
    {
        "name": "Passo Gardena (Grödner Joch)",
        "lat": 46.5497,
        "lon": 11.8089,
        "macro_region": "Trentino-Alto Adige",
        "region": "Selva di Val Gardena / Colfosco (BZ)",
        "access": "SS243 asfaltata. Valico a 2121m tra il Gruppo del Sella e le cime del Cir. Grandi parcheggi asfaltati al passo.",
        "paved": True
    },
    {
        "name": "Passo Sella",
        "lat": 46.5089,
        "lon": 11.7575,
        "macro_region": "Trentino-Alto Adige",
        "region": "Canazei / Selva di Val Gardena (TN/BZ)",
        "access": "SS242 asfaltata. Valico a 2240m tra il Sassolungo e il massiccio del Sella. Orizzonte aperto verso sud.",
        "paved": True
    },
    {
        "name": "Passo Pordoi",
        "lat": 46.4881,
        "lon": 11.8122,
        "macro_region": "Trentino-Alto Adige",
        "region": "Canazei / Fassa (TN)",
        "access": "SR48 delle Dolomiti. Valico storico a 2239m con grandi parcheggi e veduta sul Sass Pordoi e la Marmolada.",
        "paved": True
    },
    {
        "name": "Passo Rolle",
        "lat": 46.2967,
        "lon": 11.7878,
        "macro_region": "Trentino-Alto Adige",
        "region": "Primiero / Paneveggio (TN)",
        "access": "SS50 comoda. Grandi piazzali a 1989m con vista iconica sulle Pale di San Martino e il Cimon della Pala. SQM ~21.57.",
        "paved": True
    },
    {
        "name": "Passo Manghen",
        "lat": 46.1750,
        "lon": 11.4389,
        "macro_region": "Trentino-Alto Adige",
        "region": "Borgo Valsugana / Molina di Fiemme (TN)",
        "access": "SP31 attraverso la catena incontaminata del Lagorai. Piazzale al valico a 2047m presso Baita Manghen. Valle solitaria e molto buia.",
        "paved": True
    },
    {
        "name": "Passo Lavazè",
        "lat": 46.3542,
        "lon": 11.4939,
        "macro_region": "Trentino-Alto Adige",
        "region": "Varena / Val di Fiemme (TN)",
        "access": "SS620 comoda. Grande altopiano a 1808m tra Pala di Santa e Corno Bianco con ampi parcheggi in piano.",
        "paved": True
    },
    {
        "name": "Passo Costalunga (Karerpass)",
        "lat": 46.4047,
        "lon": 11.5936,
        "macro_region": "Trentino-Alto Adige",
        "region": "Nova Levante / Vigo di Fassa (BZ/TN)",
        "access": "SS241 delle Dolomiti. Valico a 1752m sotto la parete del Catinaccio e del Latemar.",
        "paved": True
    },
    {
        "name": "Alpe di Siusi (Compatsch / Saltria)",
        "lat": 46.5414,
        "lon": 11.6186,
        "macro_region": "Trentino-Alto Adige",
        "region": "Castelrotto / Alpe di Siusi (BZ)",
        "access": "Strada asfaltata da Siusi allo Sciliar (accesso libero per auto dopo le ore 17:00). Piazzali a Compatsch a 1850m. Vastità dell'altipiano e buio.",
        "paved": True
    },
    {
        "name": "Val Martello (Parcheggio Enzian / Trattla)",
        "lat": 46.5050,
        "lon": 10.7167,
        "macro_region": "Trentino-Alto Adige",
        "region": "Martello / Parco Nazionale dello Stelvio (BZ)",
        "access": "SP36 lungo la Val Martello fino al parcheggio Enzian a 2050m al capolinea della strada. Valle laterale chiusa, cielo montano limpidissimo sopra il Cevedale.",
        "paved": True
    },
    {
        "name": "Val Senales (Maso Corto / Kurzras)",
        "lat": 46.7561,
        "lon": 10.7817,
        "macro_region": "Trentino-Alto Adige",
        "region": "Senales / Alpi Venoste (BZ)",
        "access": "SP3 lungo la Val Senales fino al grande parcheggio di Maso Corto a 2011m. Circondato da vette oltre i 3000m che fungono da schermo totale per le luci urbane.",
        "paved": True
    },
    {
        "name": "Passo dello Stelvio (Stilfser Joch)",
        "lat": 46.5286,
        "lon": 10.4531,
        "macro_region": "Trentino-Alto Adige",
        "region": "Prato allo Stelvio / Bormio (BZ/SO)",
        "access": "SS38 dello Stelvio (aperta fine maggio - inizio novembre). Il valico stradale asfaltato più alto d'Italia a 2758m. Atmosfera tersissima, SQM ~21.79.",
        "paved": True
    },

    # ==========================================
    # CARINZIA - AUSTRIA (8 SITI)
    # ==========================================
    {
        "name": "Emberger Alm (Greifenburg / Drautal)",
        "lat": 46.7867,
        "lon": 13.1492,
        "macro_region": "Carinzia (Austria)",
        "region": "Greifenburg / Drautal (Kärnten - AT)",
        "access": "Strada asfaltata di montagna da Greifenburg. Uno dei siti astronomici più famosi d'Europa a 1800m, sede storica dell'Internationales Teleskoptreffen (ITT). Orizzonte sud apertissimo sulla Valle della Drava, aria tersa e buio profondo: SQM ~21.88!",
        "paved": True
    },
    {
        "name": "Nockalmstraße (Eisentalhöhe / Glockenhütte)",
        "lat": 46.8778,
        "lon": 13.7844,
        "macro_region": "Carinzia (Austria)",
        "region": "Parco Biosfera Nockberge (Kärnten - AT)",
        "access": "Strada alpina panoramica a pedaggio asfaltata (aperta maggio-ottobre). Grandi parcheggi al valico di Eisentalhöhe a 2049m. Cielo notturno tra i più bui e limpidi dell'arco alpino orientale: SQM ~21.90!",
        "paved": True
    },
    {
        "name": "Maltatal Hochalmstraße (Kölnbreinsperre / Diga)",
        "lat": 47.0783,
        "lon": 13.3361,
        "macro_region": "Carinzia (Austria)",
        "region": "Malta / Alti Tauri (Kärnten - AT)",
        "access": "Strada alpina a pedaggio attraverso la valle delle cascate fino alla mastodontica diga di Kölnbrein a 1933m. Piazzale asfaltato enorme, circondato dai ghiacciai degli Alti Tauri. SQM straordinario: ~21.93!",
        "paved": True
    },
    {
        "name": "Dobratsch / Villacher Alpe (Rosstratte)",
        "lat": 46.5986,
        "lon": 13.7194,
        "macro_region": "Carinzia (Austria)",
        "region": "Villach / Bad Bleiberg (Kärnten - AT)",
        "access": "Villacher Alpenstraße panoramica asfaltata fino all'enorme piazzale di Rosstratte a 1732m. Vista a 360° sopra le inversioni termiche del fondovalle carinziano. SQM ~21.66.",
        "paved": True
    },
    {
        "name": "Weissensee (Techendorf / Neusach)",
        "lat": 46.7167,
        "lon": 13.3000,
        "macro_region": "Carinzia (Austria)",
        "region": "Spittal an der Drau (Kärnten - AT)",
        "access": "B87 da Greifenburg o Hermagor fino alle rive del lago a 930m. Lago alpino incontaminato e protetto, senza traffico di barche a motore e bassissima illuminazione notturna. SQM ~21.75.",
        "paved": True
    },
    {
        "name": "Turracher Höhe",
        "lat": 46.9181,
        "lon": 13.8744,
        "macro_region": "Carinzia (Austria)",
        "region": "Alpi della Gurktal (Kärnten/Steiermark - AT)",
        "access": "B95 asfaltata comoda. Valico alpino con lago montano a 1795m al confine tra Carinzia e Stiria. Grandi parcheggi e orizzonte aperto. SQM ~21.74.",
        "paved": True
    },
    {
        "name": "Koralpe (Waldrast / Große Speikkogel)",
        "lat": 46.7861,
        "lon": 14.8708,
        "macro_region": "Carinzia (Austria)",
        "region": "Wolfsberg / Lavanttal (Kärnten - AT)",
        "access": "Strada asfaltata da Wolfsberg fino all'altopiano della Koralpe a 1600m. Terrazza naturale con vista aperta verso ovest e sud. SQM ~21.69.",
        "paved": True
    },
    {
        "name": "Gerlitzen Alpe (Kanzelhöhe)",
        "lat": 46.6917,
        "lon": 13.9139,
        "macro_region": "Carinzia (Austria)",
        "region": "Treffen am Ossiacher See (Kärnten - AT)",
        "access": "Strada panoramica asfaltata che sale sopra il Lago di Ossiach fino all'osservatorio solare di Kanzelhöhe a 1520m. SQM ~21.48.",
        "paved": True
    },

    # ==========================================
    # SLOVENIA OCCIDENTALE (8 SITI)
    # ==========================================
    {
        "name": "Mangartsko sedlo (Sella del Mangart)",
        "lat": 46.4442,
        "lon": 13.6425,
        "macro_region": "Slovenia Occidentale",
        "region": "Bovec / Parco Nazionale Triglav (SI)",
        "access": "Mangartska cesta: la strada asfaltata più alta della Slovenia che sale dal Passo Predil fino a 2055m nella conca terminale rocciosa sotto la cima del Mangart. Cielo mozzafiato a 360°, orizzonte sud pulitissimo verso le Giulie e l'Adriatico: SQM ~21.73!",
        "paved": True
    },
    {
        "name": "Passo del Vršič (Mojskovka / Valico)",
        "lat": 46.4350,
        "lon": 13.7436,
        "macro_region": "Slovenia Occidentale",
        "region": "Kranjska Gora / Bovec (SI)",
        "access": "Strada panoramica numero 206 (50 tornanti storici) tra Kranjska Gora e la Valle del Soča (Isonzo). Parcheggi al valico a 1611m dominati dalle pareti di Prisojnik e Mojstrovka. SQM ~21.74!",
        "paved": True
    },
    {
        "name": "Altopiano di Pokljuka (Rudno Polje)",
        "lat": 46.3458,
        "lon": 13.9236,
        "macro_region": "Slovenia Occidentale",
        "region": "Bled / Parco Nazionale Triglav (SI)",
        "access": "Ampia strada asfaltata attraverso le fitte foreste di conifere del Parco Nazionale del Triglav. Enorme piazzale di Rudno Polje a 1345m (centro sci/biathlon). Cielo scurissimo schermato dalle valli abitate. SQM ~21.74!",
        "paved": True
    },
    {
        "name": "Soriška Planina (Valico Bohinj / Železniki)",
        "lat": 46.2417,
        "lon": 14.0083,
        "macro_region": "Slovenia Occidentale",
        "region": "Bohinj / Železniki (SI)",
        "access": "Strada panoramica asfaltata numero 909 tra la valle della Sava Bohinjka e Selška dolina. Ampio parcheggio al valico a 1277m con visuale aperta sulle Giulie orientali. SQM ~21.65.",
        "paved": True
    },
    {
        "name": "Planina Kuhinja (Monte Krn / Caporetto)",
        "lat": 46.2361,
        "lon": 13.6556,
        "macro_region": "Slovenia Occidentale",
        "region": "Kobarid (Caporetto) / Monte Krn (SI)",
        "access": "Strada asfaltata panoramica da Caporetto attraverso Drežnica e Krn fino al parcheggio della malga Kuhinja a 1000m ai piedi del Monte Nero. Orizzonte sud apertissimo e buio. SQM ~21.62.",
        "paved": True
    },
    {
        "name": "Passo del Predil (Predel)",
        "lat": 46.4183,
        "lon": 13.5783,
        "macro_region": "Slovenia Occidentale",
        "region": "Tarvisio / Bovec (UD/SI)",
        "access": "SS54 / Strada 203 asfaltata e comoda. Parcheggio al valico di confine a 1156m tra Tarvisio e la Val Coritenza (Koritnica). SQM ~21.65.",
        "paved": True
    },
    {
        "name": "Altopiano della Bainsizza (Banjšice / Lokve)",
        "lat": 46.0108,
        "lon": 13.7847,
        "macro_region": "Slovenia Occidentale",
        "region": "Nova Gorica / Trnovo (SI)",
        "access": "Strada panoramica asfaltata da Nova Gorica o Tolmin. Vasto altopiano carsico boscoso a quasi 1000m, lontano dalle luci cittadine. SQM ~21.45.",
        "paved": True
    },
    {
        "name": "Trnovski gozd (Foresta di Tarnova / Predmeja / Tiha Dolina)",
        "lat": 45.9611,
        "lon": 13.8706,
        "macro_region": "Slovenia Occidentale",
        "region": "Ajdovščina / Vipava (SI)",
        "access": "Strada provinciale asfaltata che sale dal Vipacco a Predmeja e Tiha Dolina a 1080m. Altopiano fittamente boscato che funge da barriera contro le luci di pianura. SQM ~21.48.",
        "paved": True
    },

    # ==========================================
    # COSTA & LAGUNE (5 SITI)
    # ==========================================
    {
        "name": "Valle Vecchia / Brussa (Caorle)",
        "lat": 45.6267,
        "lon": 12.9617,
        "macro_region": "Costa & Lagune",
        "region": "Caorle / Valle Vecchia (VE)",
        "access": "Strada provinciale della Brussa fino al grande parcheggio dell'oasi naturale di Valle Vecchia. L'area litoranea più buia dell'Alto Adriatico: nessuna urbanizzazione né lampioni, orizzonte sud aperto sul mare a 180°! Raggiungibile in soli ~1h 05m (60 km) da Ghirano. SQM ~20.91.",
        "paved": True
    },
    {
        "name": "Delta del Po (Sacca di Scardovari / Oasi Ca' Mello)",
        "lat": 44.8967,
        "lon": 12.3833,
        "macro_region": "Costa & Lagune",
        "region": "Porto Tolle / Sacca di Scardovari (RO)",
        "access": "Strada panoramica arginale della Sacca di Scardovari. Chilometri di lagune e specchi d'acqua senza lampioni stradali né caseggiati. Orizzonte sud marino completamente aperto a perdita d'occhio: SQM ~21.25!",
        "paved": True
    },
    {
        "name": "Delta del Po (Spiaggia delle Conchiglie / Barricata)",
        "lat": 44.8483,
        "lon": 12.4650,
        "macro_region": "Costa & Lagune",
        "region": "Porto Tolle / Bocca del Po di Tolle (RO)",
        "access": "Strada arginale asfaltata fino all'imbarcadero e parcheggi della spiaggia di Barricata. Proteso verso il mare aperto con zero inquinamento luminoso a sud ed est: SQM ~21.28.",
        "paved": True
    },
    {
        "name": "Foce del Tagliamento (Bibione Pineda)",
        "lat": 45.6428,
        "lon": 13.0967,
        "macro_region": "Costa & Lagune",
        "region": "San Michele al Tagliamento (VE)",
        "access": "Parcheggio terminale verso l'area naturale protetta della foce del Tagliamento e faro. Orizzonte marino verso sud con ridotto inquinamento luminoso diretto. SQM ~20.70.",
        "paved": True
    },
    {
        "name": "Riserva Naturale Foce dell'Isonzo (Isola della Cona)",
        "lat": 45.7486,
        "lon": 13.5186,
        "macro_region": "Costa & Lagune",
        "region": "Staranzano / Grado (GO)",
        "access": "Strada asfaltata fino al parcheggio del centro visite della Riserva dell'Isola della Cona. Ampie zone umide verso il Golfo di Panzano e l'Alto Adriatico. SQM ~20.80.",
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
        "radiance_2025": None
    }

    # Interrogazione SB 2025 (Satellite VIIRS SNPP + DMSP calibrated)
    url_2025 = f"https://www.lightpollutionmap.info/api/queryraster?qk={qk}&ql=sb_2025&qt=point&qd={lon:.5f},{lat:.5f}"
    try:
        r25 = requests.get(url_2025, headers=headers, timeout=8)
        if r25.status_code == 200 and r25.text:
            parts = r25.text.split(",")
            # Formato tipico: "123;0.0524,1425" -> (radianza, elevazione)
            v_str = parts[0].split(";")[-1]
            radiance = float(v_str)
            elevation = float(parts[1]) if len(parts) > 1 else None

            # Formula standard per convertire radianza artificiale in SQM mag/arcsec²:
            # SQM = log10((radiance + 0.171168465) / 108000000) / -0.4
            sqm = math.log10((radiance + 0.171168465) / 108000000.0) / -0.4
            
            results["sqm_2025"] = round(sqm, 2)
            results["elevation_m"] = round(elevation, 0) if elevation is not None else None
            results["radiance_2025"] = round(radiance, 4)

            # Stima Bortle e NELM
            if sqm < 18.38:
                results["bortle"] = "Classe 8-9 (Cielo cittadino)"
            elif sqm < 18.94:
                results["bortle"] = "Classe 7 (Transizione suburbano/città)"
            elif sqm < 19.50:
                results["bortle"] = "Classe 6 (Cielo suburbano luminoso)"
            elif sqm < 20.49:
                results["bortle"] = "Classe 5 (Cielo suburbano)"
            elif sqm < 21.69:
                results["bortle"] = "Classe 4 (Transizione rurale/suburbano)"
            elif sqm < 21.89:
                results["bortle"] = "Classe 3 (Cielo rurale)"
            elif sqm < 21.99:
                results["bortle"] = "Classe 2 (Cielo buio tipico)"
            else:
                results["bortle"] = "Classe 1 (Cielo buio eccellente)"

            # Stima NELM (Naked Eye Limiting Magnitude)
            # Formula empirica Schaefer/Cinzano: NELM = 7.93 - 5 * log10(10^(4.316 - SQM/5) + 1)
            nelm = 7.93 - 5 * math.log10(math.pow(10, 4.316 - sqm / 5.0) + 1.0)
            results["nelm"] = round(nelm, 2)
    except Exception as e:
        pass

    # Interrogazione World Atlas 2015 (storico Falchi et al.)
    url_2015 = f"https://www.lightpollutionmap.info/api/queryraster?qk={qk}&ql=wa_2015&qt=point&qd={lon:.5f},{lat:.5f}"
    try:
        r15 = requests.get(url_2015, headers=headers, timeout=8)
        if r15.status_code == 200 and r15.text:
            parts = r15.text.split(",")
            v_str = parts[0].split(";")[-1]
            rad15 = float(v_str)
            sqm15 = math.log10((rad15 + 0.171168465) / 108000000.0) / -0.4
            results["sqm_2015"] = round(sqm15, 2)
    except Exception:
        pass

    return results


def query_driving_route(lat1: float, lon1: float, lat2: float, lon2: float) -> Dict:
    """
    Calcola il percorso stradale effettivo in automobile tra due punti con OSRM.
    Restituisce distanza in km, durata in minuti, durata formattata e tracciato geojson.
    """
    url = f"https://router.project-osrm.org/route/v1/driving/{lon1:.5f},{lat1:.5f};{lon2:.5f},{lat2:.5f}?overview=full&geometries=geojson"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            route = data["routes"][0]
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
    except Exception:
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
    Esegue le query verso LightPollutionMap e OSRM in parallelo con ThreadPoolExecutor.
    """
    if not origin:
        origin = DEFAULT_ORIGIN

    qk = generate_lpm_token()

    def process_site(site: Dict) -> Optional[Dict]:
        try:
            lpm_data = query_lpm_point(site["lat"], site["lon"], qk=qk)
            route_data = query_driving_route(origin["lat"], origin["lon"], site["lat"], site["lon"])
            sqm_val = lpm_data["sqm_2025"] if lpm_data["sqm_2025"] is not None else 0.0

            gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin['lat']},{origin['lon']}&destination={site['lat']},{site['lon']}&travelmode=driving"

            return {
                "name": site["name"],
                "macro_region": site.get("macro_region", "Altro"),
                "region": site["region"],
                "lat": site["lat"],
                "lon": site["lon"],
                "elevation_m": lpm_data["elevation_m"] if lpm_data["elevation_m"] is not None else 0,
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
        except Exception:
            return None

    print(f"Calcolo concorrente itinerari e interrogazione SQM da {origin['name']} ({len(CURATED_SITES)} siti)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        evaluated = list(executor.map(process_site, CURATED_SITES))

    results = [s for s in evaluated if s is not None and (s["sqm_2025"] or 0) >= min_sqm]
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
    <title>Mappa Siti Astronomici Bui (Triveneto, Carinzia, Slovenia)</title>
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
            width: 440px;
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
            margin-bottom: 3px;
        }}
        .badge-sqm-dark {{ background: #047857; color: #fff; }}
        .badge-sqm-high {{ background: #10b981; color: #fff; }}
        .badge-sqm-mid {{ background: #2563eb; color: #fff; }}
        .badge-sqm-violet {{ background: #7c3aed; color: #fff; }}
        .badge-sqm-amber {{ background: #d97706; color: #fff; }}
        .badge-macro {{ background: #374151; color: #93c5fd; border: 1px solid #4b5563; }}
        .badge-time {{ background: #4b5563; color: #e5e7eb; }}
        .badge-alt {{ background: #4f46e5; color: #fff; }}
        .site-title {{
            font-size: 0.95rem;
            font-weight: 600;
            margin-bottom: 4px;
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
            <h1>Siti di Osservazione Astronomica (Triveneto, Carinzia, Slovenia)</h1>
            <div class="subtitle">Partenza da Ghirano di Prata (PN) • Tempi reali stradali OSRM • Dati fotometrici LightPollutionMap 2025</div>
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

        // Inizializza mappa
        const map = L.map('map').setView([46.4, 12.8], 8);

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

        osm.addTo(map);

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
            return '#d97706'; // Ambra / Giallo scuro per SQM 20.0 - 20.99
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
                <div style="font-family: sans-serif; min-width: 210px;">
                    <h3 style="margin: 0 0 4px 0; color: #60a5fa; font-size: 1rem;">${{idx + 1}}. ${{site.name}}</h3>
                    <div style="font-size: 0.8rem; color: #9ca3af; margin-bottom: 6px;"><b>${{site.macro_region}}</b> • ${{site.region}}</div>
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
                <div class="site-region"><span class="badge badge-macro">${{site.macro_region}}</span> ${{site.region}}</div>
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

        // Adatta la visualizzazione della mappa a tutti i siti inseriti
        if (markers.length > 0) {{
            const group = L.featureGroup(markers);
            map.fitBounds(group.getBounds().pad(0.05));
        }}

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
    export_interactive_html(results, DEFAULT_ORIGIN, "sqm_dark_sites_map.html")
