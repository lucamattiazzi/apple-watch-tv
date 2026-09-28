# TV Watch

Un video sul quadrante dell’Apple Watch, ispirato al
[Seiko TV Watch del 1982](https://museum.seiko.co.jp/en/collections/watch_latestage/collect040/).

L’app include **Orbita, Eclisse, Cometa, Pulsar e Vortice**, cinque animazioni
originali di 30 secondi generate con forme geometriche, senza immagini, filmati
o musica esterni. Sono gratuite e selezionabili su iPhone e Watch.
La conversione e l’invio di video personali si sbloccano con un acquisto unico.
Configurazione e passaggio al modello gratuito: [MONETIZATION.md](MONETIZATION.md).

## Un solo video attivo

Ogni nuovo invio sostituisce il precedente. Sul Watch **Video inclusi**
permette di scegliere una delle cinque animazioni gratuite. Gli aggiornamenti dell’app conservano il video
personale già caricato. Il video precedente viene eliminato dopo che la nuova
cache è pronta; non esiste una libreria di video salvati.

Tre widget mostrano lo stesso contenuto: **Video intero**, **Video alto** e
**Video basso**. Per le due metà usare i due spazi rettangolari di Modulare Duo.
Prima di importare un video, la companion iPhone offre due stili:

- **Seiko**: 128×72 pixel, 8 livelli di grigio, per un aspetto rétro.
- **Colore**: 256×144 pixel sRGB, per più dettagli e colori.

Entrambi durano 30 secondi, senza audio, a 1 fps. I video più brevi si ripetono;
le proporzioni vengono conservate con eventuali bande nere. La scelta vale
per l’importazione successiva. Per cambiare stile al video corrente occorre
importare nuovamente l’originale. I colori delle complicazioni dipendono anche
dalla modalità di rendering e dalle impostazioni del quadrante.

App iPhone, app Watch e widget seguono le lingue preferite del dispositivo:
italiano e inglese sono inclusi, con inglese come lingua di riserva.
Le traduzioni, comprese le etichette VoiceOver e i messaggi di stato, sono in
`WatchTV/Shared/Localizable.xcstrings`. TV Watch, Orbita e i nomi dei file
personali non vengono tradotti.

## Sviluppo

Aprire `WatchTV/WatchTV.xcodeproj`, schema **FontTV**. Target: companion iPhone,
app Watch ed estensione WidgetKit. Deployment minimo: iOS 17 e watchOS 10.

```sh
xcodebuild build -project WatchTV/WatchTV.xcodeproj -scheme FontTV \
  -configuration Release -destination 'generic/platform=iOS' \
  -derivedDataPath distribution/DerivedData CODE_SIGNING_ALLOWED=NO
```

- [Origine e licenza dell’animazione](out/default/README.md).

Il repository contiene il progetto corrente, senza i prototipi precedenti.
I cinque font e le icone necessari alla compilazione sono già inclusi:
Python e `ffmpeg` servono solo per rigenerare gli asset. La compilazione richiede
macOS e Xcode con gli SDK iOS e watchOS (verificata con Xcode 26.6).

### Firma per dispositivi e distribuzione

Creare `WatchTV/Signing.local.xcconfig` e impostare `DEVELOPMENT_TEAM` con il
proprio team Apple Developer. Il file è escluso da Git e viene caricato
automaticamente dal progetto; non è necessario per compilare senza firma.
Per un proprio account configurare inoltre identificativi bundle e App Group
disponibili per quel team, mantenendoli coerenti tra i tre target, gli
entitlement e `ImportedVideo.swift`.

Archivi, log, credenziali, profili di provisioning, impostazioni personali di
firma e documenti operativi dello Store restano locali. La sorgente corrente
include la correzione di Orbita e le due modalità di conversione successive alla build 19;
non è una copia byte per byte del pacchetto inviato allo Store.

## Asset

```sh
uv sync --dev
uv run python scripts/generate_default_video.py
```

Il primo comando di generazione richiede `ffmpeg` e produce il video di
riferimento `out/default/orbita.mp4`, un’anteprima e i tre font incorporati.
Il secondo genera le maschere fisse dei widget. `make_icon.py` rigenera l’icona.

Le nuove importazioni contengono 30 PNG convertite direttamente sull’iPhone,
senza un font specifico per il video. Il Watch le salva nella cache condivisa;
i widget le mostrano con maschere a font fisso. I pacchetti precedenti con
font e Orbita restano supportati e vengono rasterizzati sul Watch. I timer sfalsati mostrano un solo frame per secondo. Prima del primo
avvio dell’app, i widget possono mostrare direttamente il font incorporato
con Orbita. Il font di un video importato non entra nella vista del widget.

Il ridisegno in Always-On e i ricaricamenti restano controllati da watchOS.
Non sono presenti streaming, server, widget diagnostici o sonde di debug.
Gli archivi di distribuzione e i backup locali sono esclusi da Git.

## Shared complication renderer

Imported video complications use [1fps-widget](https://github.com/lucamattiazzi/1fps-widget), pinned to version 0.1.0 through Swift Package Manager. Open the Xcode project and let Xcode resolve packages; no local checkout of the library is required. The `VideoWidgetLibrary` product is linked to the widget extension and supplies its mask fonts in its own resource bundle.

The provider loads full frames and lets the library crop the top/bottom variants. Orbita's bundled-font fallback, video conversion, storage and transfer remain app-owned. The extracted library needs physical-Watch verification of cold start, full/top/bottom rendering, video replacement and Always-On behavior before the next release.
