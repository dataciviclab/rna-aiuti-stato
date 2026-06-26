# RNA — Note di dominio e limiti

## Cosa rappresenta il dato

Il Registro Nazionale Aiuti di Stato (RNA) è il registro istituito presso il MIMIT che raccoglie tutte le concessioni di aiuti di Stato e aiuti De Minimis erogati da amministrazioni pubbliche italiane. Ogni mese gli enti concedenti (Ministeri, Regioni, Camere di Commercio, INPS, INAIL, ecc.) comunicano le concessioni al registro.

## Copertura

- **Periodo**: da gennaio 2017 a oggi (aggiornamento mensile)
- **Tipologie incluse**: aiuti De Minimis, aiuti notificati alla Commissione Europea, esenzioni per categoria
- **Tipologie NON incluse**: aiuti agricoli e pesca (hanno registro separato), aiuti per servizi di interesse economico generale (SGEI) sotto certe soglie
- **Soglia**: aiuti De Minimis sotto i 200.000€ (o 100.000€ per trasporto) sono inclusi solo se comunicati volontariamente? **Da verificare.**

## Limiti noti

1. **Sotto-segnalazione**: alcuni enti concedenti potrebbero non comunicare tutte le concessioni entro i termini. Il dato è completo solo per gli enti che rispettano gli obblighi di comunicazione.

2. **Soglia De Minimis**: gli aiuti De Minimis sotto una certa soglia (es. micro-aiuti) potrebbero non essere comunicati. La normativa prevede la comunicazione entro 30 giorni dalla concessione.

3. **Natura del dato**: una riga non corrisponde necessariamente a un'impresa unica. Grandi imprese con più CF/P.IVA possono apparire come beneficiari distinti.

4. **Assenza di dati di settore specifici**: agricoltura, pesca e acquacoltura hanno regimi specifici che non passano dal RNA. Per questi settori, il dato è parziale.

5. **CUP mancanti**: molti aiuti hanno CUP = "n.d." (non disponibile), rendendo difficile l'incrocio con altri dataset (es. OpenCoesione, PNRR).

## Relazione con altri dataset del Lab

| Dataset | Tipo join | Domanda |
|---------|-----------|---------|
| **ANAC bandi gara** | CF beneficiario | Le stesse imprese che vincono gare prendono anche aiuti? |
| **MEF partecipazioni** | CF | Le partecipate pubbliche ricevono aiuti? |
| **IRPEF comunale** | territorio | Relazione tra redditi e aiuti per territorio? |
| **OpenCoesione** | CUP | I progetti co-finanziati hanno anche aiuti RNA? |
| **Popolazione ISTAT** | regione | Aiuto pro-capite per regione |
| **ADE 5x1000** | CF | Gli enti del terzo settore prendono anche aiuti? |

## Aggiornamento

I file XML vengono pubblicati mensilmente sul sito www.rna.gov.it. Il batch di estrazione può essere rilancia to periodicamente per includere i nuovi mesi.
