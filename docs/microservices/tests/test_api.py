"""Tests automatiques du prototype Dar Zitouna.

Ils s'executent contre les services lances avec docker compose,
sur votre PC (pytest tests) ou dans GitHub Actions.
"""
import os

import requests

CATALOGUE = os.environ.get("CATALOGUE_URL", "http://localhost:5001")
COMMANDES = os.environ.get("COMMANDES_URL", "http://localhost:5002")
NOTIFICATIONS = os.environ.get("NOTIFICATIONS_URL", "http://localhost:5003")
SITE = os.environ.get("SITE_URL", "http://localhost:8080")


def test_les_quatre_services_sont_en_ligne():
    for url in (CATALOGUE, COMMANDES, NOTIFICATIONS, SITE):
        rep = requests.get(f"{url}/health", timeout=5)
        assert rep.status_code == 200
        assert rep.json()["status"] == "ok"


def test_le_catalogue_contient_les_produits():
    rep = requests.get(f"{CATALOGUE}/products", timeout=5)
    assert rep.status_code == 200
    produits = rep.json()
    assert len(produits) >= 5
    for p in produits:
        assert {"id", "name", "price", "stock"} <= p.keys()


def test_un_produit_inexistant_renvoie_404():
    rep = requests.get(f"{CATALOGUE}/products/9999", timeout=5)
    assert rep.status_code == 404


def test_une_commande_fait_communiquer_les_trois_services():
    produit = requests.get(f"{CATALOGUE}/products/2", timeout=5).json()

    rep = requests.post(
        f"{COMMANDES}/orders",
        json={"client": "Test CI", "product_id": 2, "quantity": 3},
        timeout=10,
    )
    assert rep.status_code == 201
    commande = rep.json()
    # Le nom et le prix viennent du service Catalogue
    assert commande["product_name"] == produit["name"]
    assert commande["total"] == round(produit["price"] * 3, 2)
    # Le service Notifications a bien repondu
    assert commande["notification"] == "envoyee"

    # La commande est enregistree dans la base du service Commandes
    commandes = requests.get(f"{COMMANDES}/orders", timeout=5).json()
    assert any(c["id"] == commande["id"] for c in commandes)

    # La notification est enregistree dans la base du service Notifications
    notifications = requests.get(f"{NOTIFICATIONS}/notifications", timeout=5).json()
    assert any(n["order_id"] == commande["id"] for n in notifications)


def test_commande_d_un_produit_inexistant_refusee():
    rep = requests.post(
        f"{COMMANDES}/orders",
        json={"client": "Test CI", "product_id": 9999, "quantity": 1},
        timeout=10,
    )
    assert rep.status_code == 404


def test_commande_incomplete_refusee():
    rep = requests.post(f"{COMMANDES}/orders", json={"quantity": 1}, timeout=5)
    assert rep.status_code == 400


def test_quantite_invalide_refusee():
    rep = requests.post(
        f"{COMMANDES}/orders",
        json={"client": "Test CI", "product_id": 1, "quantity": 0},
        timeout=5,
    )
    assert rep.status_code == 400


def test_notification_sans_message_refusee():
    rep = requests.post(f"{NOTIFICATIONS}/notify", json={}, timeout=5)
    assert rep.status_code == 400


def test_le_site_affiche_la_boutique():
    rep = requests.get(SITE, timeout=10)
    assert rep.status_code == 200
    assert "Dar Zitouna" in rep.text
    assert "Passer commande" in rep.text


def test_le_site_permet_de_commander():
    rep = requests.post(
        f"{SITE}/commander",
        data={"client": "Test CI site", "product_id": "1", "quantity": "2"},
        allow_redirects=False,
        timeout=10,
    )
    assert rep.status_code == 302
    assert "ok=" in rep.headers["Location"]
