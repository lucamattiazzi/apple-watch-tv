# Font TV

Un video sul quadrante dell’Apple Watch, ispirato al
[Seiko TV Watch del 1982](https://museum.seiko.co.jp/en/collections/watch_latestage/collect040/).

L’app include **Orbita**, un’animazione originale di 30 secondi creata con
forme geometriche, senza immagini, filmati o musica esterni. È pronta al primo
avvio e può essere sostituita con un video da Foto o File tramite la companion iPhone.

## Un solo video attivo

Ogni nuovo invio sostituisce il precedente. Sul Watch **Ripristina Orbita**
riporta al video incluso. Gli aggiornamenti dell’app conservano il video
personale già caricato. Il video precedente viene eliminato dopo che la nuova
cache è pronta; non esiste una libreria di video salvati.

Tre widget mostrano lo stesso contenuto: **Video intero**, **Video alto** e
**Video basso**. Per le due metà usare i due spazi rettangolari di Modulare Duo.
I video vengono riprodotti in scala di grigi, senza audio, a 1 fps.

App iPhone, app Watch e widget seguono le lingue preferite del dispositivo:
italiano e inglese sono inclusi, con inglese come lingua di riserva.
Le traduzioni, comprese le etichette VoiceOver e i messaggi di stato, sono in
`WatchTV/Shared/Localizable.xcstrings`. Font TV, Orbita e i nomi dei file
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
include la correzione del caricamento di Orbita successiva alla build 19;
non è una copia byte per byte del pacchetto inviato allo Store.

## Asset

```sh
uv sync --dev
uv run python scripts/generate_default_video.py
uv run python scripts/generate_gate_fonts.py
```

Il primo comando di generazione richiede `ffmpeg` e produce il video di
riferimento `out/default/orbita.mp4`, un’anteprima e i tre font incorporati.
Il secondo genera le maschere fisse dei widget. `make_icon.py` rigenera l’icona.

I widget personali utilizzano 30 PNG preparate dal Watch e maschere a font
fisso. I timer sfalsati mostrano un solo frame per secondo. Prima del primo
avvio dell’app, i widget possono mostrare direttamente il font incorporato
con Orbita. Il font di un video importato non entra nella vista del widget.

Il ridisegno in Always-On e i ricaricamenti restano controllati da watchOS.
Non sono presenti streaming, server, widget diagnostici o sonde di debug.
Gli archivi di distribuzione e i backup locali sono esclusi da Git.
