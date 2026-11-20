import os
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "notifications.db")
PORT = int(os.environ.get("PORT", 5003))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with get_db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS notifications ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "order_id INTEGER, client TEXT, message TEXT NOT NULL, "
            "created_at TEXT NOT NULL)"
        )


@app.route("/notify", methods=["POST"])
def envoyer_notification():
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    if not message:
        return jsonify({"erreur": "Le champ 'message' est obligatoire"}), 400

    date = datetime.now().isoformat(timespec="seconds")
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO notifications (order_id, client, message, created_at) "
            "VALUES (?, ?, ?, ?)",
            (data.get("order_id"), data.get("client"), message, date),
        )
        notif_id = cur.lastrowid

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
        lignes = conn.execute(
            "SELECT * FROM notifications ORDER BY id"
        ).fetchall()
    return jsonify([dict(l) for l in lignes])


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "notifications", "status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT)
