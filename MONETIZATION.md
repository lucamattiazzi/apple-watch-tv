# TV Watch: app a pagamento, tutto incluso

**Decisione del 29 settembre 2026:** TV Watch torna app a pagamento a 0,99 €, senza acquisti interni,
per poter entrare nel bundle a pagamento con AniMeteo e le altre app (un bundle a pagamento accetta solo app a pagamento).
Build 23: rimossi `VideoPurchaseStore`, `PersonalVideoAccess`, `TVWatch.storekit`, lo schema FontTV-StoreKit e il target
`PurchaseTests`. Import e invio dei video personali sono sempre disponibili; le cinque animazioni restano incluse.
L’app non è mai stata pubblicata, quindi non ci sono acquirenti dell’acquisto interno da migrare.

Da fare in App Store Connect: ritirare la submission 1.1 (22) con l’acquisto, rimuovere l’acquisto “Personal Videos Lifetime”
dalla revisione, impostare il prezzo a 0,99 € (base Italia), selezionare la build 23, aggiornare descrizioni e note di revisione, reinviare.

Storico del modello gratuito con acquisto interno (build 22), non più in uso:


Versione **1.1, build 22** caricata su App Store Connect il 29 settembre 2026.
Archivio firmato e upload riusciti. App e acquisto **Waiting for Review**,
inviati insieme il 29 settembre 2026 alle 00:28 Europe/Rome. Non pubblicata.
Submission: `2d000f51-02ca-4b3b-91dd-4f43338f81a0`.

## Cosa è già implementato

- Orbita più quattro loop originali: Eclisse, Cometa, Pulsar e Vortice.
- Scelta gratuita su iPhone e Watch, anteprima e trasferimento al Watch.
- Sblocco permanente della conversione e dell’invio dei video personali.
- StoreKit 2: prezzo localizzato dal prodotto, verifica delle transazioni,
  recupero dei diritti, ascolto degli aggiornamenti, ripristino, acquisto annullato/in attesa.
- I video già presenti restano riproducibili. Le nuove importazioni e gli invii
  personali richiedono lo sblocco; le animazioni incluse non lo richiedono.
- Ricevute App Store verificate con build originaria da 1 a 21 mantengono lo sblocco.
  Le ricevute sandbox non ottengono questa esenzione automatica.

## Configurazione App Store Connect

Il file `.storekit` serve solo per simulare acquisti in Xcode: non crea prodotti
su App Store Connect e non rende gratuita l’app pubblica.

Prodotto creato in **App Store Connect → TV Watch S → Monetizzazione → Acquisti in-app**
(Apple ID `6817124585`):

| Campo | Valore |
|---|---|
| Tipo | Non consumabile |
| Nome di riferimento | Personal Videos Lifetime |
| ID prodotto | `com.tvwatch.fonthack.personalvideos` |
| Nome italiano | Video personali |
| Descrizione italiana | Converti e invia i tuoi video. Acquisto unico. |
| Nome inglese | Personal videos |
| Descrizione inglese | Convert and send your videos. One-time purchase. |
| Prezzo Italia | 0,99 € |

Disponibilità configurata in tutti i 175 territori, con prezzi equivalenti Apple
e base Italia a 0,99 €. Il codice mostra il prezzo restituito da Apple.
Il 29 settembre il prezzo dell’app è stato portato a zero, dopo il ritiro della
vecchia submission 1.0 (20), ancora non pubblicata. Versione 1.1 con rilascio
manuale e descrizioni EN/IT aggiornate. Screenshot IAP caricato, screenshot iPhone EN/IT aggiornati e acquisto
inviato insieme alla versione 1.1 (22).

Sintesi delle note per App Review:

> Five original animations are available for free on iPhone and Apple Watch.
> The non-consumable Personal videos purchase unlocks unlimited on-device video
> conversion and transfer to the paired Watch. There is no subscription or server
> upload. Purchase and Restore purchases are in the Personal videos section of
> the iPhone app. Existing paid-app customers retain access via their verified
> original app transaction.

La prima IAP è stata presentata insieme alla versione che la utilizza.
È impostato il rilascio manuale: l’approvazione Apple non pubblica da sola l’app.
Prima del rilascio resta da verificare il flusso sandbox/TestFlight su dispositivo.

**Non rendere gratuita la vecchia build 21 prima del passaggio:** chi la scarica
riceverebbe l’esenzione prevista per gli acquirenti storici. La soglia nel codice
è il numero di build 22, non la versione commerciale 1.1. Se escono altre build
a pagamento prima della migrazione, aggiorna soglia e test. Il cambiamento di
prezzo dell’app e il rilascio della nuova versione vanno coordinati in Connect.

## Test

Apri `WatchTV/WatchTV.xcodeproj`, seleziona lo schema **FontTV-StoreKit** e un
simulatore iPhone. Lo schema usa `TVWatch.storekit`, con acquisto locale a 0,99 €:
non addebita denaro. Lo schema normale **FontTV** non usa acquisti simulati.

Il target `PurchaseTests` verifica installazione senza diritti, acquisto,
recupero in una nuova istanza, ripristino e rimborso. Eseguilo con Product → Test.
Per il test manuale usa anche acquisto annullato e Ask to Buy/in attesa e verifica
che Foto/File compaiano soltanto dopo lo sblocco. Dopo un rimborso, tornare in
primo piano deve rimuovere l’accesso ai nuovi video personali.

**Esito locale:** build iPhone/Watch/widget riuscita; asset, cache dei cinque
video, metà delle complicazioni, policy di accesso e traduzioni EN/IT verificati.
Il test transazionale è bloccato nell’ambiente corrente: StoreKitTest restituisce
`SKInternalErrorDomain Code=3` salvando la configurazione e non carica il prodotto.
Il 29 settembre, avviando **Run** da Xcode con lo schema FontTV-StoreKit,
il prodotto è stato caricato a 0,99 € e il test manuale è riuscito: acquisto
con transazione verificata, comparsa di Foto/File, ripristino tramite dialogo
Xcode e rimborso dal gestore transazioni con rimozione dello sblocco.
Il target XCTest resta bloccato con Code=3 anche dall’IDE. Il test manuale
è locale, senza addebiti: non equivale a una verifica sandbox/TestFlight.
Screenshot effettivo: `distribution/iap-review-build22.png`.

Per i controlli mirati senza StoreKit:

```sh
.venv/bin/python -m unittest discover -s tests -p test_included_videos.py
swiftc WatchTV/PhoneApp/PersonalVideoAccess.swift tests/monetization/AccessPolicyTests.swift -o /tmp/tv-access-tests
/tmp/tv-access-tests
swiftc WatchTV/Shared/ImportedVideo.swift WatchTV/Shared/IncludedVideo.swift tests/monetization/IncludedVideoTests.swift -o /tmp/tv-included-tests
/tmp/tv-included-tests WatchTV/Shared
```

Su Watch fisico: selezionare tutte le animazioni, verificare le tre complicazioni,
cambiare video durante la preparazione e provare un video personale dopo lo sblocco.

## Animazioni

Generatore riproducibile: `scripts/generate_included_videos.py` (Pillow e ffmpeg).
I quattro file `.video` sono bundle plist con 30 PNG 192×108 in scala di grigi.
Sono originali, generati da geometria e rilasciati CC0 1.0 come Orbita.
Le anteprime MP4 e il provino si rigenerano in `out/included/`:

```sh
.venv/bin/python scripts/generate_included_videos.py
```

## Documentazione Apple

- [Creare un acquisto non consumabile](https://developer.apple.com/help/app-store-connect/manage-in-app-purchases/create-consumable-or-non-consumable-in-app-purchases/)
- [Passare da app a pagamento a freemium](https://developer.apple.com/documentation/storekit/supporting-business-model-changes-by-using-the-app-transaction)
- [Inviare un acquisto alla review](https://developer.apple.com/help/app-store-connect/manage-submissions-to-app-review/submit-an-in-app-purchase/)
