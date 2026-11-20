# Dar Zitouna Cloud — Mini-projet Cloud Computing

**Cloudifier une PME e-business avec une architecture microservices**

3ème année E-business · Matière : Cloud Computing · Enseignant : M. Kais LOUKIL

Dar Zitouna est une PME tunisienne **fictive**, créée pour ce cas d'étude, qui vend en ligne des produits artisanaux (cosmétiques naturels, huiles essentielles, savons). Ce dépôt contient le prototype de sa nouvelle architecture : des microservices conteneurisés avec Docker et orchestrés avec Docker Compose.

---

## Contenu du dépôt

```
dar-zitouna-cloud/
├── docs/                    Captures d'écran des parties 2, 3 et 4
├── partie3-app/             Partie 3 : première application Flask conteneurisée
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
└── microservices/           Partie 4 : architecture microservices
    ├── docker-compose.yml
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
| Base de données | SQLite (une base par service) |
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
| Catalogue | 5001 | `GET /products`, `GET /products/{id}` | `catalogue.db` |
| Commandes | 5002 | `POST /orders`, `GET /orders` | `commandes.db` |
| Notifications | 5003 | `POST /notify`, `GET /notifications` | `notifications.db` |

Chaque service a son propre Dockerfile, sa propre base SQLite (stockée dans un volume Docker) et une API REST. Tous ont aussi une route `GET /health`.

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

Les données sont conservées dans les volumes. Pour tout effacer : `docker compose down -v`.

---

## Bonus réalisé

**Bonus 2 : Docker Compose avancé** : volumes persistants (`catalogue-data`, `commandes-data`, `notifications-data`), variables d'environnement (`PORT`, `DB_PATH`, `CATALOGUE_URL`, `NOTIFICATIONS_URL`) et réseau personnalisé (`dar-zitouna-net`).
