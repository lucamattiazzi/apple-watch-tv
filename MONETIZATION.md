# TV Watch: gratuita con video personali a pagamento

Versione preparata: **1.1, build 22**. Non ancora caricata su TestFlight o pubblicata.

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

## Configurazione App Store Connect ancora necessaria

Il file `.storekit` serve solo per simulare acquisti in Xcode: non crea prodotti
su App Store Connect e non rende gratuita l’app pubblica.

In **App Store Connect → TV Watch → Monetizzazione → Acquisti in-app**, crea:

| Campo | Valore |
|---|---|
| Tipo | Non consumabile |
| Nome di riferimento | Personal Videos Lifetime |
| ID prodotto | `com.tvwatch.fonthack.personalvideos` |
| Nome italiano | Video personali |
| Descrizione italiana | Converti e invia video personali senza limiti. Acquisto unico. |
| Nome inglese | Personal videos |
| Descrizione inglese | Convert and send unlimited personal videos. One-time purchase. |
| Prezzo Italia | 0,99 € |

Scegli disponibilità e prezzi negli altri territori. Il codice mostra il prezzo
restituito da Apple, senza imporre 0,99 in tutte le valute. Completa eventuali
accordi fiscali/bancari richiesti, screenshot della schermata di sblocco e
informazioni per la review. Questi dati non sono stati modificati automaticamente.

Note per App Review, da adattare dopo i test:

> Five original animations are available for free on iPhone and Apple Watch.
> The non-consumable Personal videos purchase unlocks unlimited on-device video
> conversion and transfer to the paired Watch. There is no subscription or server
> upload. Purchase and Restore purchases are in the Personal videos section of
> the iPhone app. Existing paid-app customers retain access via their verified
> original app transaction.

La prima IAP va presentata insieme alla versione dell’app che la utilizza.
Carica la build, associa l’acquisto alla versione e completa il test sandbox
prima di inviarli alla review. Usa un rilascio manuale per coordinare il passaggio.

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
Non è stato verificato un acquisto reale, sandbox o locale riuscito. Risolvere
questo test e provare il prodotto sandbox prima della pubblicazione.

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
