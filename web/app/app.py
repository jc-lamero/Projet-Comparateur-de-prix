import os
import re
import unicodedata
from collections import defaultdict
from datetime import datetime

import pymysql
from flask import Flask, render_template, request, abort

app = Flask(__name__)

# -------------------------
# DB
# -------------------------
def db_conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "db"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "app"),
        password=os.getenv("DB_PASSWORD", "app"),
        database=os.getenv("DB_NAME", "comparateur"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        charset="utf8mb4",
    )

# -------------------------
# Normalisation produit
# -------------------------
def normalize_name(s: str) -> str:
    """
    Transforme un nom produit en "clé" stable pour matcher entre sites
    (ex: "Samsung SSD 990 PRO M.2 ... 1 To" ~ "Samsung SSD 990 Pro 1 To").
    """
    s = s or ""

    # enlever accents
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.lower()

    # uniformiser unités
    s = s.replace(" to", "tb").replace(" go", "gb")
    s = re.sub(r"\b(\d+)\s*tb\b", r"\1tb", s)
    s = re.sub(r"\b(\d+)\s*gb\b", r"\1gb", s)

    # enlever ponctuation
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    # stopwords (on enlève du bruit)
    stop = {"ssd", "disque", "interne", "nvme", "pcie", "m2", "m", "2", "sata"}
    tokens = [t for t in s.split() if t not in stop]

    # limiter pour éviter les clés trop longues
    return " ".join(tokens[:12])

def pick_image(items):
    # priorité: image de l'offre la moins chère, sinon 1ère image dispo
    cheapest = min(items, key=lambda x: x["price_cents"])
    if cheapest.get("image_url"):
        return cheapest["image_url"]
    for it in items:
        if it.get("image_url"):
            return it["image_url"]
    return None

def get_sources(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT source FROM products ORDER BY source ASC;")
        return [r["source"] for r in cur.fetchall()]

def fetch_all_products(limit=3000):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT source, name, price_cents, url, image_url, scraped_at
                FROM products
                ORDER BY scraped_at DESC
                LIMIT {int(limit)}
            """)
            rows = cur.fetchall()
        sources = get_sources(conn)
    return rows, sources

# -------------------------
# ROUTES
# -------------------------
@app.get("/")
def best():
    q = request.args.get("q", "").strip()
    source_filter = request.args.get("source", "").strip()
    sort = request.args.get("sort", "price").strip()  # price | recent

    rows, sources = fetch_all_products(limit=3000)

    # Filtrage léger côté Python (simple & robuste)
    if source_filter:
        rows = [r for r in rows if r["source"] == source_filter]

    if q:
        q_low = q.lower()
        rows = [r for r in rows if q_low in (r["name"] or "").lower()]

    # Grouping par "clé normalisée" (LA correction principale)
    groups = defaultdict(list)
    for r in rows:
        key = normalize_name(r["name"])
        r["key"] = key
        groups[key].append(r)

    data = []
    for key, items in groups.items():
        cheapest = min(items, key=lambda x: x["price_cents"])
        img = pick_image(items)

        # nom affiché: celui du cheapest (ou le premier)
        display_name = cheapest["name"] or items[0]["name"]

        data.append({
            "key": key,
            "name": display_name,
            "image_url": img,
            "items": items,
            "cheapest": cheapest,
        })

    if sort == "recent":
        # tri sur la date la plus récente du groupe
        def group_last_scrape(g):
            return max(i["scraped_at"] for i in g["items"] if i["scraped_at"] is not None)
        data.sort(key=group_last_scrape, reverse=True)
    else:
        data.sort(key=lambda g: g["cheapest"]["price_cents"])

    return render_template(
        "best.html",
        data=data,
        now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        sources=sources,
        q=q,
        source=source_filter,
        sort=sort,
    )


@app.get("/details")
def details():
    # IMPORTANT: on ne passe plus un "name", on passe la clé normalisée
    key = request.args.get("key", "").strip()
    if not key:
        abort(400, "Missing key")

    rows, _ = fetch_all_products(limit=5000)

    items = [r for r in rows if normalize_name(r["name"]) == key]

    if not items:
        return render_template("details.html", name="Produit introuvable", items=[], cheapest=None)

    items.sort(key=lambda x: x["price_cents"])
    cheapest = items[0]
    title = cheapest["name"]

    return render_template("details.html", name=title, items=items, cheapest=cheapest)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
