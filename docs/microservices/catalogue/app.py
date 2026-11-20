import os
import time

import psycopg
from flask import Flask, jsonify
from psycopg.rows import dict_row

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 5001))
# Adresse de la base PostgreSQL du service (fournie par docker-compose.yml)
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://dar_zitouna:dar_zitouna_mdp@localhost:5432/catalogue_db"
)

PRODUITS_INITIAUX = [
    ("Savon a l'huile d'olive de Sfax", 8.0, 120),
    ("Huile d'argan pure 50 ml", 35.0, 40),
    ("Eau de rose distillee 100 ml", 12.0, 75),
    ("Huile essentielle de romarin 10 ml", 18.0, 60),
    ("Savon au ghassoul", 9.0, 90),
]


def get_db():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def init_db():
    # PostgreSQL peut mettre quelques secondes a demarrer : on reessaie
    for _ in range(30):
        try:
            with get_db() as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS products ("
                    "id SERIAL PRIMARY KEY, name TEXT NOT NULL, "
                    "price DOUBLE PRECISION NOT NULL, stock INTEGER NOT NULL)"
                )
                nb = conn.execute("SELECT COUNT(*) AS nb FROM products").fetchone()["nb"]
                if nb == 0:
                    with conn.cursor() as cur:
                        cur.executemany(
                            "INSERT INTO products (name, price, stock) VALUES (%s, %s, %s)",
                            PRODUITS_INITIAUX,
                        )
            return
        except psycopg.OperationalError:
            print("En attente de PostgreSQL...", flush=True)
            time.sleep(2)
    raise RuntimeError("Impossible de se connecter a PostgreSQL")


@app.route("/products", methods=["GET"])
def liste_produits():
    with get_db() as conn:
        lignes = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    return jsonify(lignes)


@app.route("/products/<int:product_id>", methods=["GET"])
def un_produit(product_id):
    with get_db() as conn:
        ligne = conn.execute(
            "SELECT * FROM products WHERE id = %s", (product_id,)
        ).fetchone()
    if ligne is None:
        return jsonify({"erreur": "Produit introuvable"}), 404
    return jsonify(ligne)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"service": "catalogue", "status": "ok"})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=PORT)
