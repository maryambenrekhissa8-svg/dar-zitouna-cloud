# Dar Zitouna Cloud — Mini-projet Cloud Computing

**Cloudifier une PME e-business avec une architecture microservices**

3ème année E-business · Matière : Cloud Computing · Enseignant : M. Kais LOUKIL

Dar Zitouna est une PME tunisienne **fictive**, créée pour ce cas d'étude, qui vend en ligne des produits artisanaux (cosmétiques naturels, huiles essentielles, savons). Ce dépôt contient le prototype de sa nouvelle architecture : des microservices conteneurisés avec Docker et orchestrés avec Docker Compose.

---

## Contenu du dépôt

```
dar-zitouna-cloud/
├── .github/workflows/
│   └── ci.yml               Bonus 3 : pipeline CI/CD GitHub Actions
├── docs/                    Captures d'écran des parties 2, 3 et 4
├── partie3-app/             Partie 3 : première application Flask conteneurisée
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
└── microservices/           Partie 4 : architecture microservices
    ├── docker-compose.yml
    ├── postgres/init.sql    Bonus 1 : création des 3 bases PostgreSQL
    ├── tests/test_api.py    Bonus 3 : tests automatiques
    ├── catalogue/           Service Catalogue (port 5001)
    ├── commandes/           Service Commandes (port 5002)
    ├── notifications/       Service Notifications (port 5003)
    └── site/                Site web de la boutique (port 8080)
```

## Technologies

| Ressource | Solution |
| --- | --- |
| Environnement d'exécution | Docker Desktop |
| Conteneurisation | Docker |
| Orchestration | Docker Compose |
| Langage / framework | Python 3.12 / Flask |
| Base de données | PostgreSQL 16 dans un conteneur (une base par service) |
| CI/CD | GitHub Actions |
| Gestion du code | GitHub |

---

## Partie 3 : application Docker

```bash
cd partie3-app
docker build -t mon-app .
docker run -p 8000:8000 mon-app
```

Puis ouvrir http://localhost:8000. Arrêter avec `Ctrl + C`.

---

## Partie 4 : architecture microservices

### Les services

| Service | Port | Routes | Base de données |
| --- | --- | --- | --- |
| Catalogue | 5001 | `GET /products`, `GET /products/{id}` | `catalogue_db` |
| Commandes | 5002 | `POST /orders`, `GET /orders` | `commandes_db` |
| Notifications | 5003 | `POST /notify`, `GET /notifications` | `notifications_db` |

Chaque service a son propre Dockerfile, sa propre base de données PostgreSQL et une API REST. Tous ont aussi une route `GET /health`.

Un conteneur **postgres** (PostgreSQL 16) héberge les trois bases séparées : `catalogue_db`, `commandes_db` et `notifications_db`. Chaque service ne se connecte qu'à sa propre base. Les données sont stockées dans le volume `postgres-data`.

Un quatrième conteneur, **site** (port 8080), est le site web de la boutique : il affiche les produits, permet de commander avec un formulaire et montre les commandes et les notifications, en appelant les trois microservices. Il n'a pas de base de données.

### Communication entre les services

Quand une commande est créée (`POST /orders`), le service **Commandes** :

1. appelle **Catalogue** (`GET http://catalogue:5001/products/{id}`) pour vérifier le produit et récupérer son prix ;
2. calcule le total et enregistre la commande dans sa base ;
3. appelle **Notifications** (`POST http://notifications:5003/notify`) pour prévenir le client.

Les services se trouvent sur le réseau Docker personnalisé `dar-zitouna-net` et s'appellent par leur nom.

### Lancer le projet

```bash
cd microservices
docker compose up -d --build
docker ps
```

### Tester

Le plus simple : ouvrir le site web sur http://localhost:8080 et passer une commande avec le formulaire.

Les API sont aussi accessibles directement :

- http://localhost:5001/products : liste des produits
- http://localhost:5002/orders : liste des commandes
- http://localhost:5003/notifications : liste des notifications

Passer une commande (PowerShell) :

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:5002/orders -ContentType "application/json" -Body '{"client": "Amira", "product_id": 2, "quantity": 3}'
```

La réponse contient `"notification": "envoyee"`, et le message apparaît ensuite sur http://localhost:5003/notifications.

### Arrêter

```bash
docker compose down
```

Les données sont conservées dans le volume `postgres-data`. Pour tout effacer : `docker compose down -v`.

### Lancer les tests automatiques

Avec les services démarrés :

```bash
cd microservices
pip install pytest requests
pytest -v tests
```

Les 10 tests vérifient que les services sont en ligne, que le catalogue répond, qu'une commande fait communiquer les trois microservices, que les erreurs sont bien gérées et que le site permet de commander.

---

## Bonus réalisés

| Bonus | Réalisation |
| --- | --- |
| **Bonus 1 : base de données** | PostgreSQL 16 dans un conteneur Docker (`postgres`), avec une base séparée par microservice, créée par `postgres/init.sql` |
| **Bonus 2 : Docker Compose avancé** | Volume persistant `postgres-data`, variables d'environnement (`PORT`, `DATABASE_URL`, `CATALOGUE_URL`, `COMMANDES_URL`, `NOTIFICATIONS_URL`), réseau personnalisé `dar-zitouna-net`, vérification de santé (`healthcheck`) de PostgreSQL |
| **Bonus 3 : CI/CD** | Pipeline GitHub Actions (`.github/workflows/ci.yml`) qui, à chaque `git push`, construit les images Docker, démarre les services et lance les 10 tests automatiques. Résultat visible dans l'onglet **Actions** du dépôt |
