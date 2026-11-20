import os
import sqlite3
from datetime import datetime

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "commandes.db")
PORT = int(os.environ.get("PORT", 5002))
# Adresses des autres services sur le reseau Docker
CATALOGUE_URL = os.environ.get("CATALOGUE_URL", "http://catalogue:5001")
NOTIFICATIONS_URL = os.environ.get("NOTIFICATIONS_URL", "http://notifications:5003")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with get_db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS orders ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "client TEXT NOT NULL, product_id INTEGER NOT NULL, "
            "product_name TEXT NOT NULL, quantity INTEGER NOT NULL, "
            "total REAL NOT NULL, created_at TEXT NOT NULL)"
        )


@app.route("/orders", methods=["POST"])
def creer_commande():
    data = request.get_json(silent=True) or {}
    client = data.get("client")
    product_id = data.get("product_id")
    quantity = data.get("quantity", 1)

    if not client or not isinstance(product_id, int):
        return jsonify({"erreur": "Champs obligatoires : client (texte) et product_id (nombre)"}), 400
    if not isinstance(quantity, int) or quantity < 1:
        return jsonify({"erreur": "La quantite doit etre un nombre entier positif"}), 400

    # 1. Appel au service Catalogue pour verifier le produit
    try:
        rep = requests.get(f"{CATALOGUE_URL}/products/{product_id}", timeout=5)
    except requests.RequestException:
        return jsonify({"erreur": "Service Catalogue indisponible"}), 503
    if rep.status_code == 404:
        return jsonify({"erreur": f"Le produit {product_id} n'existe pas"}), 404
    produit = rep.json()

    # 2. Calcul du total et enregistrement de la commande
    total = round(produit["price"] * quantity, 2)
    date = datetime.now().isoformat(timespec="seconds")
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO orders (client, product_id, product_name, quantity, total, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (client, product_id, produit["name"], quantity, total, date),
        )
        order_id = cur.lastrowid

    # 3. Appel au service Notifications pour prevenir le client
    message = (f"Commande {order_id} confirmee : {quantity} x {produit['name']}, "
               f"total {total} DT")
    try:
        rep_notif = requests.post(
            f"{NOTIFICATIONS_URL}/notify",
            json={"order_id": order_id, "client": client, "message": message},
            timeout=5,
        )
        notification = "envoyee" if rep_notif.status_code == 201 else "echec"
    except requests.RequestException:
        notification = "echec"

    return jsonify({
        "id": order_id,
        "client": client,
        "product_id": product_id,
        "product_name": produit["name"],
        "quantity": quantity,
        "total": total,
        "created_at": date,
        "notification": notification,
    }), 201


@app.route("/orders", methods=["GET"])
def liste_commandes():
    with get_db() as conn:
        lignes = conn.execute("SELECT * FROM orders ORDER BY id").fetchall()
    return jsonify([dict(l) for l in lignes])


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "commandes", "status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT)
