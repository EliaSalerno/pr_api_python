import requests

BASE = "http://127.0.0.1:8000"


def crea(payload):
    r = requests.post(f"{BASE}/items", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


def elenca(limit=50, offset=0):
    r = requests.get(f"{BASE}/items", params={"limit": limit, "offset": offset}, timeout=10)
    r.raise_for_status()
    return r.json()


def leggi(item_id):
    r = requests.get(f"{BASE}/items/{item_id}", timeout=10)
    r.raise_for_status()
    return r.json()


def sostituisci(item_id, payload):
    r = requests.put(f"{BASE}/items/{item_id}", json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


def elimina(item_id):
    r = requests.delete(f"{BASE}/items/{item_id}", timeout=10)
    r.raise_for_status()


if __name__ == "__main__":
    nuovo = crea({"nome": "Mario", "età": 30, "tags": ["a", "b"]})
    print("Creato:", nuovo)

    crea([1, 2, 3])                      # anche una lista va bene
    crea({"annidato": {"x": [1, {"y": None}]}})

    print("Lettura:", leggi(nuovo["id"]))
    print("Aggiorno:", sostituisci(nuovo["id"], {"nome": "Luigi"}))
    print("Elenco:", elenca())

    elimina(nuovo["id"])
    print("Dopo eliminazione:", elenca())