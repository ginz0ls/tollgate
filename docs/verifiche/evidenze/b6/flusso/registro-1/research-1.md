## Letto nel progetto
- web/index.html
- web/styles.css
- tests/test_page.py
- src/components/StatusBadge.tsx
- docs/superpowers/plans/2026-11-11-pulsante-salva.md

## Nessuna fonte esterna
Il diff usa solo HTML, JavaScript del browser senza librerie (getElementById, textContent) e unittest della libreria standard Python: nessuna libreria o servizio esterno.

## Cosa ho trovato
Il modulo #appunto ha un solo submit "Invia" e nessuno script. styles.css ha gia' stili per button e focus-visible con variabili: non serve modificarlo. Aggiungo button#salva type=button con aria-label e span aria-hidden, p#salvato role=status vuoto, script defer, e web/app.js che scrive "Salvato". Test nuovi in tests/test_save_button.py con un parser html.parser; il test esistente di test_page non va toccato. Il test del componente SaveButton.tsx e' del Task 2, fuori scope qui. Nessun componente nuovo in questo task (solo markup statico).
esito: valida
