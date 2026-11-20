import os

import requests
from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

PORT = int(os.environ.get("PORT", 8080))
CATALOGUE_URL = os.environ.get("CATALOGUE_URL", "http://catalogue:5001")
COMMANDES_URL = os.environ.get("COMMANDES_URL", "http://commandes:5002")
NOTIFICATIONS_URL = os.environ.get("NOTIFICATIONS_URL", "http://notifications:5003")

SERVICES = [
    ("Catalogue", CATALOGUE_URL, 5001),
    ("Commandes", COMMANDES_URL, 5002),
    ("Notifications", NOTIFICATIONS_URL, 5003),
]

# Apparence de chaque produit (couleur et initiales), par numero de produit
STYLES = {
    1: ("#6b7a3a", "SO"),
    2: ("#c8963e", "AR"),
    3: ("#c96f7e", "RO"),
    4: ("#4f8a7a", "RM"),
    5: ("#8a6a52", "GH"),
}


def get_json(url):
    """Appelle un service et renvoie (donnees, erreur)."""
    try:
        rep = requests.get(url, timeout=3)
        rep.raise_for_status()
        return rep.json(), None
    except requests.RequestException:
        return None, "indisponible"


PAGE = """
<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dar Zitouna - Boutique artisanale</title>
<style>
  :root {
    --olive: #4f5d2a; --olive-light: #6b7a3a; --sand: #f7f1e5; --cream: #fffdf8;
    --terra: #c0663a; --ink: #2d2a24; --muted: #7a7266; --line: #e8dfcf;
    --ok: #3f8a4f; --ko: #b9473a;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: "Segoe UI", Arial, sans-serif; color: var(--ink); background: var(--sand); }
  h1, h2, h3 { font-family: Georgia, "Times New Roman", serif; margin: 0; }
  a { color: inherit; }

  header.hero {
    background: linear-gradient(135deg, var(--olive) 0%, #6f7f36 60%, var(--terra) 140%);
    color: #fff; padding: 48px 24px 64px; text-align: center; position: relative; overflow: hidden;
  }
  .hero .logo { display: inline-flex; align-items: center; gap: 12px; margin-bottom: 14px; }
  .hero .leaf { width: 44px; height: 44px; }
  .hero h1 { font-size: 46px; letter-spacing: 1px; }
  .hero p { font-size: 18px; opacity: .92; margin: 10px auto 0; max-width: 620px; line-height: 1.5; }
  .badge-docker { display: inline-block; margin-top: 18px; padding: 6px 14px; border-radius: 999px;
                  background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.35); font-size: 13px; }

  main { max-width: 1120px; margin: -36px auto 48px; padding: 0 20px; position: relative; }

  .status { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; margin-bottom: 28px; }
  .chip { background: var(--cream); border: 1px solid var(--line); border-radius: 999px; padding: 8px 16px;
          font-size: 14px; box-shadow: 0 4px 14px rgba(60,50,30,.08); display: flex; align-items: center; gap: 8px; }
  .dot { width: 10px; height: 10px; border-radius: 50%; }
  .dot.ok { background: var(--ok); box-shadow: 0 0 0 4px rgba(63,138,79,.18); }
  .dot.ko { background: var(--ko); box-shadow: 0 0 0 4px rgba(185,71,58,.18); }
  .chip small { color: var(--muted); }

  .alert { border-radius: 12px; padding: 14px 18px; margin-bottom: 24px; font-size: 15px; }
  .alert.ok { background: #e6f2e4; border: 1px solid #b9d9b3; color: #2f6b3a; }
  .alert.ko { background: #f8e4e0; border: 1px solid #e7b9b0; color: #8f3529; }

  section { margin-bottom: 40px; }
  .section-title { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 16px; }
  .section-title h2 { font-size: 28px; color: var(--olive); }
  .section-title span { color: var(--muted); font-size: 14px; }

  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 18px; }
  .card { background: var(--cream); border: 1px solid var(--line); border-radius: 16px; overflow: hidden;
          box-shadow: 0 6px 18px rgba(60,50,30,.07); transition: transform .15s ease; }
  .card:hover { transform: translateY(-3px); }
  .card .visual { height: 110px; display: flex; align-items: center; justify-content: center;
                  font-family: Georgia, serif; font-size: 34px; color: #fff; letter-spacing: 2px; }
  .card .body { padding: 14px 16px 16px; }
  .card h3 { font-size: 17px; line-height: 1.3; min-height: 44px; }
  .card .price { font-size: 22px; font-weight: 700; color: var(--terra); margin-top: 8px; }
  .card .stock { font-size: 13px; color: var(--muted); margin-top: 2px; }
  .card .ref { font-size: 12px; color: var(--muted); }

  .two { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  @media (max-width: 860px) { .two { grid-template-columns: 1fr; } .hero h1 { font-size: 34px; } }

  .panel { background: var(--cream); border: 1px solid var(--line); border-radius: 16px; padding: 22px;
           box-shadow: 0 6px 18px rgba(60,50,30,.07); }
  form label { display: block; font-size: 14px; color: var(--muted); margin: 12px 0 6px; }
  form input, form select { width: 100%; padding: 11px 12px; border: 1px solid var(--line); border-radius: 10px;
                            font-size: 15px; background: #fff; }
  form button { margin-top: 18px; width: 100%; padding: 13px; border: 0; border-radius: 10px; cursor: pointer;
                background: var(--terra); color: #fff; font-size: 16px; font-weight: 600; }
  form button:hover { background: #a9552d; }
  .hint { font-size: 13px; color: var(--muted); margin-top: 10px; line-height: 1.5; }

  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th { text-align: left; color: var(--muted); font-weight: 600; padding: 8px 6px; border-bottom: 2px solid var(--line); }
  td { padding: 10px 6px; border-bottom: 1px solid var(--line); }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
  .empty { color: var(--muted); font-style: italic; padding: 12px 0; }

  .notif { display: flex; gap: 12px; padding: 12px 0; border-bottom: 1px solid var(--line); }
  .notif:last-child { border-bottom: 0; }
  .notif .icon { flex: none; width: 36px; height: 36px; border-radius: 50%; background: #eef2e2;
                 display: flex; align-items: center; justify-content: center; color: var(--olive); font-size: 18px; }
  .notif .who { font-weight: 600; }
  .notif .msg { font-size: 14px; margin-top: 2px; }
  .notif .when { font-size: 12px; color: var(--muted); margin-top: 2px; }

  footer { text-align: center; color: var(--muted); font-size: 13px; padding: 24px; border-top: 1px solid var(--line); }
</style>
</head>
<body>

<header class="hero">
  <div class="logo">
    <svg class="leaf" viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <path d="M8 40C8 20 22 8 42 6c-2 20-14 34-34 34Z" fill="rgba(255,255,255,.9)"/>
      <path d="M10 38C20 28 28 20 38 10" stroke="#4f5d2a" stroke-width="2.5" stroke-linecap="round"/>
    </svg>
    <h1>Dar Zitouna</h1>
  </div>
  <p>Savons, huiles essentielles et cosmétiques naturels, faits à la main à Sfax.</p>
  <div class="badge-docker">Prototype microservices &middot; Docker Compose</div>
</header>

<main>

  <div class="status">
    {% for s in statuts %}
      <div class="chip"><span class="dot {{ 'ok' if s.ok else 'ko' }}"></span>
        Service {{ s.nom }} <small>:{{ s.port }} &middot; {{ 'en ligne' if s.ok else 'hors ligne' }}</small></div>
    {% endfor %}
  </div>

  {% if ok %}
    <div class="alert ok">Commande n&deg;{{ ok }} enregistrée. Le service Commandes a vérifié le produit auprès du
      Catalogue, puis a demandé au service Notifications de prévenir le client.</div>
  {% endif %}
  {% if erreur %}<div class="alert ko">{{ erreur }}</div>{% endif %}

  <section>
    <div class="section-title"><h2>Nos produits</h2><span>fournis par le service Catalogue</span></div>
    {% if produits %}
      <div class="grid">
        {% for p in produits %}
          <div class="card">
            <div class="visual" style="background: {{ p.couleur }};">{{ p.initiales }}</div>
            <div class="body">
              <div class="ref">Produit n&deg;{{ p.id }}</div>
              <h3>{{ p.name }}</h3>
              <div class="price">{{ '%.0f' % p.price }} DT</div>
              <div class="stock">{{ p.stock }} en stock</div>
            </div>
          </div>
        {% endfor %}
      </div>
    {% else %}
      <div class="alert ko">Le service Catalogue est indisponible.</div>
    {% endif %}
  </section>

  <div class="two">
    <section class="panel">
      <div class="section-title"><h2>Passer commande</h2></div>
      <form method="post" action="{{ url_for('commander') }}">
        <label for="client">Votre nom</label>
        <input id="client" name="client" required placeholder="Ex. : Yassine">
        <label for="product_id">Produit</label>
        <select id="product_id" name="product_id">
          {% for p in produits or [] %}
            <option value="{{ p.id }}">{{ p.name }} - {{ '%.0f' % p.price }} DT</option>
          {% endfor %}
        </select>
        <label for="quantity">Quantité</label>
        <input id="quantity" name="quantity" type="number" min="1" value="1" required>
        <button type="submit">Commander</button>
        <p class="hint">La commande est envoyée au service Commandes (port 5002), qui interroge le Catalogue
          puis prévient le service Notifications.</p>
      </form>
    </section>

    <section class="panel">
      <div class="section-title"><h2>Notifications</h2><span>service Notifications</span></div>
      {% if notifications %}
        {% for n in notifications %}
          <div class="notif">
            <div class="icon">&#9993;</div>
            <div>
              <div class="who">{{ n.client }}</div>
              <div class="msg">{{ n.message }}</div>
              <div class="when">{{ n.created_at.replace('T', ' à ') }} (UTC)</div>
            </div>
          </div>
        {% endfor %}
      {% elif notifications is none %}
        <div class="alert ko">Le service Notifications est indisponible.</div>
      {% else %}
        <div class="empty">Aucune notification pour le moment.</div>
      {% endif %}
    </section>
  </div>

  <section class="panel" style="margin-top: 24px;">
    <div class="section-title"><h2>Dernières commandes</h2><span>service Commandes</span></div>
    {% if commandes %}
      <table>
        <tr><th>N&deg;</th><th>Client</th><th>Produit</th><th class="num">Quantité</th><th class="num">Total</th></tr>
        {% for c in commandes %}
          <tr><td>{{ c.id }}</td><td>{{ c.client }}</td><td>{{ c.product_name }}</td>
              <td class="num">{{ c.quantity }}</td><td class="num">{{ '%.0f' % c.total }} DT</td></tr>
        {% endfor %}
      </table>
    {% elif commandes is none %}
      <div class="alert ko">Le service Commandes est indisponible.</div>
    {% else %}
      <div class="empty">Aucune commande pour le moment.</div>
    {% endif %}
  </section>

</main>

<footer>Dar Zitouna &middot; Mini-projet Cloud Computing &middot; 4 conteneurs sur le réseau dar-zitouna-net</footer>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def accueil():
    produits, _ = get_json(f"{CATALOGUE_URL}/products")
    commandes, _ = get_json(f"{COMMANDES_URL}/orders")
    notifications, _ = get_json(f"{NOTIFICATIONS_URL}/notifications")

    if produits:
        for p in produits:
            couleur, initiales = STYLES.get(p["id"], ("#6b7a3a", p["name"][:2].upper()))
            p["couleur"], p["initiales"] = couleur, initiales

    statuts = []
    for nom, url, port in SERVICES:
        _, err = get_json(f"{url}/health")
        statuts.append({"nom": nom, "port": port, "ok": err is None})

    return render_template_string(
        PAGE,
        produits=produits,
        commandes=list(reversed(commandes))[:8] if commandes else commandes,
        notifications=list(reversed(notifications))[:6] if notifications else notifications,
        statuts=statuts,
        ok=request.args.get("ok"),
        erreur=request.args.get("erreur"),
    )


@app.route("/commander", methods=["POST"])
def commander():
    try:
        donnees = {
            "client": request.form.get("client", "").strip(),
            "product_id": int(request.form.get("product_id", 0)),
            "quantity": int(request.form.get("quantity", 1)),
        }
    except ValueError:
        return redirect(url_for("accueil", erreur="Quantité ou produit invalide."))

    try:
        rep = requests.post(f"{COMMANDES_URL}/orders", json=donnees, timeout=5)
    except requests.RequestException:
        return redirect(url_for("accueil", erreur="Le service Commandes est indisponible."))

    if rep.status_code == 201:
        return redirect(url_for("accueil", ok=rep.json()["id"]))
    message = rep.json().get("erreur", "La commande a échoué.")
    return redirect(url_for("accueil", erreur=message))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
