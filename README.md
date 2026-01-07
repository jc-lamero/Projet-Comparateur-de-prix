# Comparateur de prix SSD (Scrapy + Docker)

## 🎯 Objectif
Réaliser un comparateur de prix permettant de déterminer, pour chaque produit (SSD), quel site propose le prix le moins cher.

Le projet utilise :
- Scrapy pour le scraping
- MySQL pour le stockage des données
- Docker & Docker Compose pour l’orchestration
- Un serveur web (Flask) pour l’affichage

---

## 🛒 Sites comparés
- LDLC
- TopAchat

*(D’autres sites ont été étudiés mais certains bloquent le scraping via robots.txt)*

---

## 🧱 Architecture
Le projet est composé de plusieurs conteneurs Docker :

- **db** : base de données MySQL
- **scraper** : Scrapy (récupération des produits)
- **web** : serveur web Flask (affichage des résultats)

Chaque service possède son propre `Dockerfile`.

---

## 🗃️ Données récupérées
Pour chaque produit :
- Nom
- Prix
- Lien vers la page produit
- Source (site marchand)
- Date de récupération

Les données sont stockées dans une base MySQL contenue dans un conteneur Docker.

---

## 🌐 Affichage
- Page principale : **Meilleurs prix**
  - 1 produit = 1 ligne
  - Affiche uniquement l’offre la moins chère
- Page **Détails** :
  - Affiche toutes les offres disponibles pour un produit
- Les produits sont cliquables et redirigent vers le site marchand

---

## 🚀 Lancement du projet
Un seul script permet de tout lancer :

```bash
./run.sh
