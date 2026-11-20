import os
import time
from datetime import datetime

import psycopg
import requests
from flask import Flask, jsonify, request
from psycopg.rows import dict_row

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 5002))
# Adresse de la base PostgreSQL du service (fournie par docker-compose.yml)
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://dar_zitouna:dar_zitouna_mdp@localhost:5432/commandes_db"
)
# Adresses des autres services sur le reseau Docker
CATALOGUE_URL = os.environ.get("CATALOGUE_URL", "http://catalogue:5001")
NOTIFICATIONS_URL = os.environ.get("NOTIFICATIONS_URL", "http://notifications:5003")


def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    # PostgreSQL peut mettre quelques secondes a demarrer : on reessaie
    for _ in range(30):
        try:
            with get_db() as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS orders ("
                    "id SERIAL PRIMARY KEY, client TEXT NOT NULL, "
                    "product_id INTEGER NOT NULL, product_name TEXT NOT NULL, "
                    "quantity INTEGER NOT NULL, total DOUBLE PRECISION NOT NULL, "
                    "created_at TEXT NOT NULL)"
                )
            return
        except psycopg.OperationalError:
            print("En attente de PostgreSQL...", flush=True)
            time.sleep(2)
    raise RuntimeError("Impossible de se connecter a PostgreSQL")


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
        order_id = conn.execute(
            "INSERT INTO orders (client, product_id, product_name, quantity, total, created_at) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (client, product_id, produit["name"], quantity, total, date),
        ).fetchone()["id"]

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
    return jsonify(lignes)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "commandes", "status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT)
