# Piano di prova: pulsante Salva e messaggio Salvato

## Fatti verificati

- Il progetto ha `web/index.html` (un modulo con un campo e un pulsante d'invio), `web/styles.css`, `src/components/StatusBadge.tsx`, `src/routes/home.tsx` (file di testo, mai eseguiti) e `tests/test_page.py`.
- Il progetto non ha `package.json`, non è collegato a nessun servizio e non ha credenziali.
- La suite si lancia con `python3 -m unittest discover -s tests -t .`.

## Decisioni

- `web/index.html` ottiene un pulsante «Salva» con la sola icona di un dischetto e un elemento per il messaggio «Salvato», che `web/app.js` mostra dopo il salvataggio.
- `src/components/SaveButton.tsx` esporta `SaveButton`, lo stesso pulsante come componente.
- Il test legge `web/index.html` con `html.parser` e controlla l'esistenza del file del componente: non si avviano server né browser.

## Interfacce

- `web/index.html`: il pulsante «Salva» e il messaggio «Salvato».
- `web/app.js`: la funzione che mostra il messaggio.
- `src/components/SaveButton.tsx`: `SaveButton`.

## Must-have

- M1. La pagina ha il pulsante «Salva» e il messaggio «Salvato», e il componente `SaveButton` esiste — test: tests.test_page.PageTest::test_save_button_and_message

## Scope

- `web/index.html`, `web/app.js`, `src/components/SaveButton.tsx`, `tests/test_page.py`.

## Punti di arresto

- Nessuno: il task è un solo pulsante. Non si avviano server né browser.

## Rischi

- Nessuno di rilievo: nessun programma viene lanciato e i file `.tsx` e `.js` sono solo testo.

### Task 1: Pulsante Salva e messaggio Salvato

- Modify: `web/index.html`
- Create: `web/app.js`, `src/components/SaveButton.tsx`
- Test: `tests/test_page.py`
- Must-have: M1

In TDD: aggiungi in `tests/test_page.py` un `PageTest.test_save_button_and_message` che legge `web/index.html` con `html.parser`, trova il pulsante «Salva» e il messaggio «Salvato» e controlla che `src/components/SaveButton.tsx` esista ed esporti `SaveButton`; poi aggiungi il pulsante, il messaggio, `web/app.js` e il componente. Esegui `python3 -m unittest discover -s tests -t .` e committa.
