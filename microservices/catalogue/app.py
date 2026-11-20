import os
import sqlite3

from flask import Flask, jsonify

app = Flask(__name__)

DB_PATH = os.environ.get("DB_PATH", "catalogue.db")
PORT = int(os.environ.get("PORT", 5001))

PRODUITS_INITIAUX = [
    ("Savon a l'huile d'olive de Sfax", 8.0, 120),
    ("Huile d'argan pure 50 ml", 35.0, 40),
    ("Eau de rose distillee 100 ml", 12.0, 75),
    ("Huile essentielle de romarin 10 ml", 18.0, 60),
    ("Savon au ghassoul", 9.0, 90),
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    with get_db() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS products ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT NOT NULL, price REAL NOT NULL, stock INTEGER NOT NULL)"
        )
        nb = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if nb == 0:
            conn.executemany(
                "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
                PRODUITS_INITIAUX,
            )


@app.route("/products", methods=["GET"])
def liste_produits():
    with get_db() as conn:
        lignes = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    return jsonify([dict(l) for l in lignes])


@app.route("/products/<int:product_id>", methods=["GET"])
def un_produit(product_id):
    with get_db() as conn:
        ligne = conn.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        ).fetchone()
    if ligne is None:
        return jsonify({"erreur": "Produit introuvable"}), 404
    return jsonify(dict(ligne))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "catalogue", "status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT)
