import os
import time
from datetime import datetime

import psycopg
from flask import Flask, jsonify, request
from psycopg.rows import dict_row

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 5003))
# Adresse de la base PostgreSQL du service (fournie par docker-compose.yml)
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://dar_zitouna:dar_zitouna_mdp@localhost:5432/notifications_db"
)


def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    # PostgreSQL peut mettre quelques secondes a demarrer : on reessaie
    for _ in range(30):
        try:
            with get_db() as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS notifications ("
                    "id SERIAL PRIMARY KEY, order_id INTEGER, client TEXT, "
                    "message TEXT NOT NULL, created_at TEXT NOT NULL)"
                )
            return
        except psycopg.OperationalError:
            print("En attente de PostgreSQL...", flush=True)
            time.sleep(2)
    raise RuntimeError("Impossible de se connecter a PostgreSQL")


@app.route("/notify", methods=["POST"])
def envoyer_notification():
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    if not message:
        return jsonify({"erreur": "Le champ 'message' est obligatoire"}), 400

    date = datetime.now().isoformat(timespec="seconds")
    with get_db() as conn:
        notif_id = conn.execute(
            "INSERT INTO notifications (order_id, client, message, created_at) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (data.get("order_id"), data.get("client"), message, date),
        ).fetchone()["id"]

    # Dans un vrai systeme, on enverrait ici un e-mail ou un SMS.
    print(f"[NOTIFICATION] {data.get('client')} : {message}", flush=True)

    return jsonify({
        "id": notif_id,
        "order_id": data.get("order_id"),
        "client": data.get("client"),
        "message": message,
        "created_at": date,
        "statut": "envoyee",
    }), 201


@app.route("/notifications", methods=["GET"])
def liste_notifications():
    with get_db() as conn:
        lignes = conn.execute("SELECT * FROM notifications ORDER BY id").fetchall()
    return jsonify(lignes)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "notifications", "status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT)
