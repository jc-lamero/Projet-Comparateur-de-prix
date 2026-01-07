#!/usr/bin/env bash
set -euo pipefail

echo " Build des images..."
docker compose build

echo " Démarrage DB + Web..."
docker compose up -d db web phpmyadmin

echo " Petite attente DB (3s)..."
sleep 3

echo " (Optionnel) nettoyage de la table products"
# docker compose exec -T db mysql -uapp -papp -D comparateur -e "TRUNCATE TABLE products;"

echo " Scrape LDLC (SSD)..."
docker compose run --rm scraper bash -lc "cd price_comparator && scrapy crawl ldlc_ssd -L INFO"

echo " Scrape TopAchat (SSD)..."
docker compose run --rm scraper bash -lc "cd price_comparator && scrapy crawl topachat_ssd -L INFO"

echo " Scrape Materiel.net (SSD)..."
docker compose run --rm scraper bash -lc "cd price_comparator && scrapy crawl materielnet_ssd -L INFO"


echo " OK. Vérif rapide :"
docker compose exec -T db mysql -uapp -papp -D comparateur -e \
"SELECT source, COUNT(*) AS n FROM products GROUP BY source;"

echo ""
echo " Site dispo ici : http://localhost:8080/"
echo " PhpMyAdmin : http://localhost:8081/"
