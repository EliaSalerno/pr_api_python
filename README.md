# API JSON con FastAPI, SQLite e requests

Progetto didattico: un **server** che riceve JSON qualsiasi e lo salva in SQLite, e un **client** che lo usa. Questo README spiega:

1. la teoria sulle API
2. le librerie usate
3. il codice di `server.py` e `client.py` riga per riga

---

## Indice

1. [Struttura del progetto e avvio](#1-struttura-del-progetto-e-avvio)
2. [Teoria sulle API](#2-teoria-sulle-api)
3. [Le librerie usate](#3-le-librerie-usate)
4. [server.py riga per riga](#4-serverpy-riga-per-riga)
5. [client.py riga per riga](#5-clientpy-riga-per-riga)
6. [Provare l'API con curl](#6-provare-lapi-con-curl)
7. [Limiti e miglioramenti possibili](#7-limiti-e-miglioramenti-possibili)

---

## 1. Struttura del progetto e avvio

```
.
├── server.py     # API REST (FastAPI + SQLite)
├── client.py     # client che chiama l'API (requests)
├── data.db       # database SQLite (creato al primo avvio)
└── README.md
```

```bash
pip install fastapi uvicorn requests

uvicorn server:app --reload     # terminale 1: avvia il server
python client.py                # terminale 2: esegue il client
```

Documentazione interattiva generata automaticamente: <http://127.0.0.1:8000/docs>

Flusso di una richiesta:

```
client.py ──HTTP POST /items + JSON──▶ Uvicorn ──▶ FastAPI ──▶ crea() ──▶ SQLite (data.db)
client.py ◀──── 201 Created + JSON ──────────────────────────────────────────────┘
```

---

## 2. Teoria sulle API

### 2.1 Cos'è un'API

Un'**API** (*Application Programming Interface*) è un'interfaccia che definisce **come due programmi comunicano**. Chi la espone dichiara cosa si può chiedere e in che formato; chi la usa non deve sapere come funziona l'implementazione interna.

Una **Web API** usa il protocollo HTTP: un programma (client) manda una richiesta a un altro (server) attraverso la rete e riceve una risposta.

### 2.2 Modello client-server

- Il **client** inizia sempre la comunicazione (invia una richiesta).
- Il **server** resta in ascolto, elabora e risponde.
- Sono indipendenti: il client può essere scritto in qualsiasi linguaggio (Python, JavaScript, app mobile) purché parli HTTP.

### 2.3 HTTP: anatomia di richiesta e risposta

**Richiesta**

```
POST /items HTTP/1.1                 ← metodo + percorso (+ versione)
Host: 127.0.0.1:8000                 ← header
Content-Type: application/json       ← header: formato del body
                                     ← riga vuota
{"nome": "Mario", "età": 30}         ← body
```

**Risposta**

```
HTTP/1.1 201 Created                 ← status code + descrizione
Content-Type: application/json       ← header
                                     ← riga vuota
{"id": 1, "ricevuto": {...}}         ← body
```

Elementi:

| Elemento | Funzione |
|---|---|
| **URL** | Indirizzo della risorsa: schema (`http`), host (`127.0.0.1`), porta (`8000`), percorso (`/items/1`), query string (`?limit=10`) |
| **Metodo** | L'azione da compiere |
| **Header** | Metadati: tipo di contenuto, autenticazione, lingua, ecc. |
| **Body** | I dati veri e propri (assente in genere in `GET` e `DELETE`) |
| **Status code** | L'esito dell'operazione |

### 2.4 Metodi HTTP e operazioni CRUD

| Metodo | CRUD | Significato | Idempotente | Safe |
|---|---|---|---|---|
| `GET` | Read | Legge una risorsa o una lista | Sì | Sì |
| `POST` | Create | Crea una nuova risorsa | No | No |
| `PUT` | Update | Sostituisce una risorsa **per intero** | Sì | No |
| `PATCH` | Update | Modifica **parzialmente** | Dipende | No |
| `DELETE` | Delete | Elimina | Sì | No |

- **Idempotente**: ripetere la stessa richiesta N volte ha lo stesso effetto di farla una volta. Due `POST` identici creano due risorse; due `DELETE` della stessa risorsa lasciano il server nello stesso stato.
- **Safe**: la richiesta non modifica dati sul server.

### 2.5 Status code

| Classe | Significato | Esempi |
|---|---|---|
| **1xx** | Informativi | 101 Switching Protocols |
| **2xx** | Successo | 200 OK, 201 Created, 204 No Content |
| **3xx** | Redirezione | 301 Moved Permanently, 304 Not Modified |
| **4xx** | Errore del **client** | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 422 Unprocessable Entity, 429 Too Many Requests |
| **5xx** | Errore del **server** | 500 Internal Server Error, 502 Bad Gateway, 503 Service Unavailable |

In questo progetto: `201` alla creazione, `204` all'eliminazione, `404` se l'`id` non esiste, `422` se la richiesta è malformata (ad esempio un `id` non numerico).

### 2.6 JSON

**JSON** (*JavaScript Object Notation*) è il formato testuale più usato per scambiare dati. Tipi supportati:

| JSON | Python |
|---|---|
| oggetto `{...}` | `dict` |
| array `[...]` | `list` |
| stringa `"..."` | `str` |
| numero | `int` / `float` |
| `true` / `false` | `True` / `False` |
| `null` | `None` |

Due operazioni fondamentali:
- **serializzazione**: oggetto Python → testo JSON (`json.dumps`)
- **deserializzazione**: testo JSON → oggetto Python (`json.loads`)

### 2.7 REST

**REST** (*Representational State Transfer*) è uno stile architetturale per le API web. Principi:

1. **Risorse identificate da URL**: `/items` (collezione), `/items/42` (singolo elemento). Nomi, non verbi: l'azione la decide il metodo HTTP.
2. **Interfaccia uniforme**: si usano i metodi HTTP con il loro significato standard.
3. **Stateless**: ogni richiesta contiene tutte le informazioni necessarie; il server non conserva la "sessione" del client tra una richiesta e l'altra.
4. **Rappresentazioni**: la risorsa viene scambiata in un formato (qui JSON).
5. **Client-server** separati e, opzionalmente, **cache** e architettura a strati.

Mappatura nel nostro progetto:

| Operazione | Metodo + URL | Esito |
|---|---|---|
| Crea | `POST /items` | 201 |
| Elenca | `GET /items?limit=50&offset=0` | 200 |
| Leggi uno | `GET /items/{id}` | 200 / 404 |
| Sostituisci | `PUT /items/{id}` | 200 / 404 |
| Elimina | `DELETE /items/{id}` | 204 / 404 |

### 2.8 Parametri: path, query, body

| Tipo | Dove | Esempio | Nel codice |
|---|---|---|---|
| **Path parameter** | Dentro l'URL | `/items/42` | `item_id: int` |
| **Query parameter** | Dopo `?` | `/items?limit=10` | `limit: int = 50` |
| **Body** | Corpo della richiesta | `{"nome": "Mario"}` | `payload: Any = Body(...)` |

### 2.9 Altri concetti utili

- **Autenticazione**: dimostrare chi si è (API key, Basic auth, Bearer token/JWT, OAuth 2.0). Non implementata in questo progetto.
- **HTTPS**: HTTP cifrato con TLS; obbligatorio in produzione.
- **CORS**: regole del browser su quali domini possono chiamare un'API.
- **Rate limiting**: limite al numero di richieste per client (risposta `429`).
- **Paginazione**: restituire le liste a blocchi (`limit` e `offset`), come in `GET /items`.
- **Versionamento**: `/v1/items`, per evolvere l'API senza rompere i client esistenti.
- **OpenAPI/Swagger**: standard per descrivere un'API; FastAPI lo genera da solo e lo mostra su `/docs`.
- **Timeout**: tempo massimo di attesa di una risposta; senza timeout un client può bloccarsi all'infinito.

### 2.10 Altri stili di API

| Stile | Caratteristica |
|---|---|
| **SOAP** | Basato su XML, molto formale, tipico dell'ambito enterprise |
| **GraphQL** | Un solo endpoint; il client specifica i campi che vuole |
| **gRPC** | Binario (Protocol Buffers), molto veloce, usato tra microservizi |
| **WebSocket** | Canale bidirezionale persistente per il tempo reale |

---

## 3. Le librerie usate

### 3.1 Librerie della standard library (già incluse in Python)

| Libreria | Ruolo nel progetto |
|---|---|
| `json` | Converte tra oggetti Python e testo JSON (`dumps` / `loads`) |
| `sqlite3` | Interfaccia al database SQLite, un database su singolo file senza server dedicato |
| `contextlib` | Fornisce `closing`, che garantisce la chiusura della connessione |
| `typing` | Fornisce `Any`, il tipo "qualsiasi valore" |

### 3.2 Librerie esterne

| Libreria | Ruolo | Installazione |
|---|---|---|
| **FastAPI** | Framework per costruire API: routing, validazione dei parametri, conversione automatica in JSON, documentazione OpenAPI | `pip install fastapi` |
| **Uvicorn** | Server ASGI: apre la porta, riceve le connessioni HTTP e passa le richieste a FastAPI | `pip install uvicorn` |
| **requests** | Client HTTP per Python: invia richieste e legge le risposte | `pip install requests` |

Nota: FastAPI si appoggia a due librerie che vengono installate automaticamente: **Starlette** (gestione HTTP e routing) e **Pydantic** (validazione dei dati).

### 3.3 FastAPI e Uvicorn: chi fa cosa

```
Rete ─▶ Uvicorn (server) ─▶ FastAPI (applicazione) ─▶ le tue funzioni (crea, leggi, ...)
```

- **Uvicorn** si occupa del livello di rete: socket, parsing HTTP.
- **FastAPI** decide quale funzione chiamare in base a metodo e percorso, valida i parametri e costruisce la risposta.
- Il comando `uvicorn server:app` significa: "dal file `server.py` (modulo `server`) prendi l'oggetto chiamato `app`".

### 3.4 Perché SQLite

SQLite è un database relazionale contenuto in un solo file (`data.db`). Non richiede installazione né un processo server separato, ed è ideale per prototipi, strumenti locali e applicazioni piccole. Per molti scrittori concorrenti o carichi elevati si passa a PostgreSQL o MySQL.

---

## 4. server.py riga per riga

### 4.1 Import

```python
import json
```
Importa il modulo per convertire tra oggetti Python e stringhe JSON. Serve perché SQLite non conosce i dict: salviamo il JSON come testo.

```python
import sqlite3
```
Importa il driver per SQLite.

```python
from contextlib import closing
```
Importa `closing`, un *context manager* che chiama `.close()` su un oggetto all'uscita da un blocco `with`. Serve perché la connessione di `sqlite3`, usata con `with`, non si chiude da sola (vedi 4.3).

```python
from typing import Any
```
`Any` indica "qualsiasi tipo". Lo usiamo per dire che il body può essere un oggetto, una lista, una stringa, un numero.

```python
from fastapi import Body, FastAPI, HTTPException
```
- `FastAPI`: la classe che rappresenta l'applicazione.
- `Body`: indica che un parametro va letto dal corpo della richiesta.
- `HTTPException`: eccezione che FastAPI trasforma in una risposta HTTP di errore con lo status code scelto.

### 4.2 Configurazione

```python
DB_PATH = "data.db"
```
Nome del file del database. Come percorso relativo, viene creato nella cartella da cui si avvia il server. Metterlo in una costante evita di ripeterlo.

```python
app = FastAPI(title="JSON API + SQLite")
```
Crea l'applicazione. L'oggetto `app` è quello che Uvicorn cerca. Il `title` compare nella documentazione su `/docs`.

### 4.3 Connessione al database

```python
def get_conn() -> sqlite3.Connection:
```
Funzione che crea e restituisce una nuova connessione. L'annotazione `-> sqlite3.Connection` indica il tipo restituito (solo documentazione).

```python
    conn = sqlite3.connect(DB_PATH)
```
Apre il file `data.db`, creandolo se non esiste.

```python
    conn.row_factory = sqlite3.Row
```
Per impostazione predefinita le righe sono tuple (`row[0]`). Con `sqlite3.Row` si accede anche per nome (`row["data"]`), più leggibile e robusto.

```python
    return conn
```
Restituisce la connessione.

**Perché una connessione per richiesta?** FastAPI esegue le funzioni `def` normali in un pool di thread, e per default una connessione SQLite può essere usata solo dal thread che l'ha creata. Aprire una connessione breve a ogni richiesta evita errori di thread ed è semplice; per SQLite il costo è trascurabile.

### 4.4 Creazione della tabella

```python
def init_db() -> None:
```
Funzione che prepara il database. `-> None` indica che non restituisce nulla.

```python
    with closing(get_conn()) as conn, conn:
```
Riga importante, sono due context manager in una riga sola:
1. `closing(get_conn()) as conn`: apre la connessione e la chiude **alla fine**.
2. `conn`: usare la connessione stessa come context manager fa **commit** se il blocco finisce bene, **rollback** se c'è un'eccezione. Non la chiude.

Ordine di uscita: prima commit/rollback, poi close.

```python
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                data       TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
```
Esegue la query SQL:
- `CREATE TABLE IF NOT EXISTS items`: crea la tabella solo se non esiste, quindi si può rieseguire senza errori.
- `id INTEGER PRIMARY KEY AUTOINCREMENT`: identificativo numerico univoco, assegnato in automatico e mai riutilizzato.
- `data TEXT NOT NULL`: qui va il JSON come stringa; `NOT NULL` vieta il valore vuoto.
- `created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP`: data di inserimento, compilata dal database.

```python
init_db()
```
Chiamata a livello di modulo: viene eseguita una volta, quando Uvicorn importa `server.py`, quindi la tabella esiste prima della prima richiesta.

### 4.5 POST /items (crea)

```python
@app.post("/items", status_code=201)
```
**Decoratore**: registra la funzione sotto come gestore delle richieste `POST /items`. `status_code=201` imposta lo status di successo (`Created`) al posto del 200 predefinito.

```python
def crea(payload: Any = Body(...)):
```
- `payload` è il JSON ricevuto, già convertito in oggetto Python (dict, list, ecc.).
- `Any` accetta qualsiasi struttura.
- `Body(...)` dice a FastAPI di leggerlo dal corpo della richiesta; i tre puntini (`...`, *Ellipsis*) significano "parametro obbligatorio".

```python
    """Riceve un JSON qualsiasi (oggetto, lista, valore) e lo salva."""
```
Docstring: FastAPI la mostra come descrizione dell'endpoint in `/docs`.

```python
    with closing(get_conn()) as conn, conn:
```
Apre la connessione con commit automatico e chiusura finale (come in 4.4).

```python
        cur = conn.execute("INSERT INTO items (data) VALUES (?)", (json.dumps(payload),))
```
- `json.dumps(payload)` trasforma l'oggetto Python in stringa JSON.
- Il `?` è un **segnaposto**: il valore viene passato a parte, nella tupla. Questo previene la **SQL injection**, perché il driver tratta il valore come dato e mai come codice SQL. Non costruire mai query con f-string o concatenazione con dati dell'utente.
- `(json.dumps(payload),)`: la **virgola finale** è obbligatoria, altrimenti Python non crea una tupla ma una semplice stringa tra parentesi.
- Restituisce un *cursor*, da cui leggiamo l'id.

```python
        return {"id": cur.lastrowid, "ricevuto": payload}
```
`cur.lastrowid` è l'`id` assegnato dal database alla riga appena inserita. FastAPI converte il dict restituito in JSON e lo invia con status 201. Il commit avviene all'uscita dal `with`.

### 4.6 GET /items (elenca)

```python
@app.get("/items")
def elenca(limit: int = 50, offset: int = 0):
```
Gestore di `GET /items`. I parametri `limit` e `offset` non compaiono nel percorso e non sono `Body`, quindi FastAPI li legge dalla **query string** (`/items?limit=10&offset=20`). Gli annotati `int` fanno validare e convertire il valore automaticamente (se non è un numero, risposta 422). I valori dopo `=` sono i default.

```python
    with closing(get_conn()) as conn:
```
Solo lettura: serve `closing` ma non il commit.

```python
        rows = conn.execute(
            "SELECT id, data, created_at FROM items ORDER BY id LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
```
- `ORDER BY id`: ordine stabile.
- `LIMIT ? OFFSET ?`: **paginazione**; `limit` è quante righe restituire, `offset` quante saltarne.
- `.fetchall()` legge tutte le righe del risultato in una lista.

```python
    return [
        {"id": r["id"], "created_at": r["created_at"], "data": json.loads(r["data"])}
        for r in rows
    ]
```
*List comprehension* che costruisce, per ogni riga, un dict. `json.loads(r["data"])` riporta la stringa salvata a oggetto Python, così la risposta contiene JSON vero e non una stringa con le virgolette escapate. Notare che la `return` è fuori dal `with`: la connessione è già chiusa, ma i dati sono già in memoria.

### 4.7 GET /items/{item_id} (leggi uno)

```python
@app.get("/items/{item_id}")
def leggi(item_id: int):
```
`{item_id}` nel percorso è un **path parameter**: FastAPI lo estrae dall'URL e lo converte in `int` grazie all'annotazione. Chiamando `/items/abc` risponde 422 senza eseguire la funzione.

```python
    with closing(get_conn()) as conn:
        r = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
```
`fetchone()` restituisce una sola riga, oppure `None` se non c'è nessun risultato.

```python
    if r is None:
        raise HTTPException(404, "Non trovato")
```
Se la riga non esiste, solleva un'eccezione che FastAPI converte in risposta `404` con corpo `{"detail": "Non trovato"}`.

```python
    return {"id": r["id"], "created_at": r["created_at"], "data": json.loads(r["data"])}
```
Restituisce l'elemento con il JSON deserializzato.

### 4.8 PUT /items/{item_id} (sostituisci)

```python
@app.put("/items/{item_id}")
def sostituisci(item_id: int, payload: Any = Body(...)):
```
Combina un path parameter (`item_id`) e un body (`payload`).

```python
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "UPDATE items SET data = ? WHERE id = ?", (json.dumps(payload), item_id)
        )
```
Sostituisce il contenuto della riga con `id` indicato. L'ordine dei valori nella tupla deve corrispondere a quello dei `?`.

```python
        if cur.rowcount == 0:
            raise HTTPException(404, "Non trovato")
```
`cur.rowcount` è il numero di righe modificate. Se è 0, l'`id` non esiste e si risponde 404. L'eccezione dentro il `with` provoca un **rollback** (qui non c'è nulla da annullare) e poi la chiusura.

```python
    return {"id": item_id, "ricevuto": payload}
```
Conferma con i dati ricevuti.

### 4.9 DELETE /items/{item_id} (elimina)

```python
@app.delete("/items/{item_id}", status_code=204)
def elimina(item_id: int):
```
Lo status `204 No Content` indica successo senza corpo nella risposta.

```python
    with closing(get_conn()) as conn, conn:
        cur = conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "Non trovato")
```
Elimina la riga; se non ne è stata toccata nessuna, l'elemento non esisteva e si risponde 404. Non c'è `return`: la funzione restituisce `None` e, con 204, FastAPI invia una risposta vuota.

---

## 5. client.py riga per riga

### 5.1 Setup

```python
import requests
```
Importa la libreria client HTTP.

```python
BASE = "http://127.0.0.1:8000"
```
URL di base del server. `127.0.0.1` è l'indirizzo locale (*localhost*), `8000` la porta predefinita di Uvicorn. Per usare un server remoto basta cambiare questa riga.

### 5.2 crea

```python
def crea(payload):
    r = requests.post(f"{BASE}/items", json=payload, timeout=10)
```
- `requests.post(...)` invia una richiesta `POST`.
- `f"{BASE}/items"` è una **f-string** che compone l'URL `http://127.0.0.1:8000/items`.
- `json=payload` serializza l'oggetto Python in JSON e imposta l'header `Content-Type: application/json`. Per questo il client accetta dict, liste e qualunque struttura serializzabile.
- `timeout=10`: dopo 10 secondi senza risposta solleva un'eccezione. **Senza timeout `requests` può attendere all'infinito.**
- `r` è un oggetto `Response`.

```python
    r.raise_for_status()
```
Se lo status è 4xx o 5xx solleva `requests.HTTPError`. Così gli errori non passano inosservati.

```python
    return r.json()
```
Legge il corpo della risposta e lo converte da JSON a oggetto Python.

### 5.3 elenca

```python
def elenca(limit=50, offset=0):
    r = requests.get(f"{BASE}/items", params={"limit": limit, "offset": offset}, timeout=10)
```
`params=` aggiunge la query string all'URL (`/items?limit=50&offset=0`) occupandosi della codifica dei caratteri speciali. Il resto è come in `crea`.

```python
    r.raise_for_status()
    return r.json()
```

### 5.4 leggi

```python
def leggi(item_id):
    r = requests.get(f"{BASE}/items/{item_id}", timeout=10)
    r.raise_for_status()
    return r.json()
```
Inserisce l'`id` nel percorso. Se l'elemento non esiste il server risponde 404 e `raise_for_status()` solleva l'eccezione.

### 5.5 sostituisci

```python
def sostituisci(item_id, payload):
    r = requests.put(f"{BASE}/items/{item_id}", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()
```
Metodo `PUT`, con `id` nel percorso e il nuovo JSON nel body.

### 5.6 elimina

```python
def elimina(item_id):
    r = requests.delete(f"{BASE}/items/{item_id}", timeout=10)
    r.raise_for_status()
```
Il server risponde 204 senza corpo, quindi non c'è `r.json()` da chiamare (fallirebbe su un body vuoto).

### 5.7 Programma di prova

```python
if __name__ == "__main__":
```
Il blocco viene eseguito solo se il file è lanciato direttamente (`python client.py`), non se viene importato come modulo da un altro file.

```python
    nuovo = crea({"nome": "Mario", "età": 30, "tags": ["a", "b"]})
    print("Creato:", nuovo)
```
Crea un elemento e stampa la risposta, che contiene l'`id` assegnato.

```python
    crea([1, 2, 3])                      # anche una lista va bene
    crea({"annidato": {"x": [1, {"y": None}]}})
```
Dimostra che il server accetta JSON di qualsiasi forma: una lista, un oggetto annidato, un `None` (che in JSON diventa `null`).

```python
    print("Lettura:", leggi(nuovo["id"]))
    print("Aggiorno:", sostituisci(nuovo["id"], {"nome": "Luigi"}))
    print("Elenco:", elenca())
```
Legge l'elemento creato, lo sostituisce con un nuovo JSON e stampa l'elenco completo.

```python
    elimina(nuovo["id"])
    print("Dopo eliminazione:", elenca())
```
Elimina il primo elemento e verifica che non compaia più nell'elenco.

---

## 6. Provare l'API con curl

```bash
# Crea
curl -X POST http://127.0.0.1:8000/items \
     -H "Content-Type: application/json" \
     -d '{"nome": "Mario", "età": 30}'

# Elenca (con paginazione)
curl "http://127.0.0.1:8000/items?limit=10&offset=0"

# Leggi
curl http://127.0.0.1:8000/items/1

# Sostituisci
curl -X PUT http://127.0.0.1:8000/items/1 \
     -H "Content-Type: application/json" \
     -d '{"nome": "Luigi"}'

# Elimina
curl -X DELETE http://127.0.0.1:8000/items/1 -i
```

Per ispezionare il database direttamente:

```bash
sqlite3 data.db "SELECT * FROM items;"
```

---

## 7. Limiti e miglioramenti possibili

- **Nessuna autenticazione**: chiunque raggiunga il server può leggere e scrivere. Aggiungere API key o JWT.
- **Nessuna validazione dello schema**: accetta qualsiasi JSON per scelta. Per dati con struttura nota, usare modelli **Pydantic** (`class Utente(BaseModel): ...`).
- **Una connessione per richiesta**: semplice e sicuro con SQLite; per carichi alti usare un pool o un database server.
- **Nessun `PATCH`**: si può solo sostituire per intero.
- **Ricerca nel JSON**: SQLite offre `json_extract(data, '$.nome')` per filtrare sui campi interni.
- **HTTPS e CORS**: da configurare in produzione (reverse proxy come Nginx, `CORSMiddleware` di FastAPI).
- **Test automatici**: `fastapi.testclient.TestClient` con `pytest`.
- **Gestione errori nel client**: catturare `requests.exceptions.RequestException` per gestire timeout e server non raggiungibile.