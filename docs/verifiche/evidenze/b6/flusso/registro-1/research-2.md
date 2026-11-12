## Letto nel progetto
- src/components/StatusBadge.tsx
- tests/test_save_button.py
- web/index.html
- web/app.js
- web/styles.css

## Documentazione
- https://react.dev/reference/react-dom/components/common — onClick riceve una funzione; gli attributi aria-* si scrivono come in HTML (aria-label su un button con sola icona).

## Cosa ho trovato
Non c'è package.json: la versione di React non è dichiarata (documentazione corrente react.dev). Il markup del pulsante è già in web/index.html (type=button, aria-label=Salva, span aria-hidden con 💾); il componente lo replica con onClick={onSave}. StatusBadge usa props tipizzate con type e export function: lo seguo. Nessuno stile in linea né colori a mano. Il repo non ha test dei componenti tsx (solo Python sul testo), quindi il test richiesto è quello testuale del task.
esito: valida
