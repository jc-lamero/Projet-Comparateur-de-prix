import os
import re
import hashlib
from collections import defaultdict
from datetime import datetime

import pymysql
from flask import Flask, render_template, request

app = Flask(__name__)

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

def normalize_name(name: str) -> str:
    if not name:
        return ""
    s = name.lower().strip()

    # uniformiser séparateurs / espaces
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s)

    # enlever mots très génériques qui cassent le matching inter-sites
    s = re.sub(r"\bssd\b", "", s)
    s = re.sub(r"\bsérie\b", "", s)
    s = re.sub(r"\bseries\b", "", s)

    # uniformiser To/Go
    s = s.replace("1to", "1 to").replace("2to", "2 to").replace("4to", "4 to")
    s = s.replace("go", " go").replace("to", " to")
    s = re.sub(r"\s+", " ", s).strip()

    return s


def group_id(key: str) -> str:
    return hashlib.md5(key.encode("utf-8")).hexdigest()[:12]

@app.get("/")
def best_prices():
    q = request.args.get("q", "").strip()
    source = request.args.get("source", "").strip()

    where = []
    params = []
    if source:
        where.append("source = %s")
        params.append(source)
    if q:
        where.append("name LIKE %s")
        params.append(f"%{q}%")

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT source, name, price_cents, url, image_url, scraped_at
                FROM products
                {where_sql}
                ORDER BY scraped_at DESC
                
            """, params)
            rows = cur.fetchall()

    # group by normalized name
    groups = defaultdict(list)
    for r in rows:
        key = normalize_name(r["name"])
        groups[key].append(r)

    data = []
    for key, items in groups.items():
        items_sorted = sorted(items, key=lambda x: x["price_cents"])
        cheapest = items_sorted[0]
        second = items_sorted[1] if len(items_sorted) >= 2 else None

        gap_cents = None
        gap_pct = None
        if second:
            gap_cents = second["price_cents"] - cheapest["price_cents"]
            if cheapest["price_cents"] > 0:
                gap_pct = (gap_cents / cheapest["price_cents"]) * 100

        data.append({
            "gid": group_id(key),
            "name": items_sorted[0]["name"],   # affichage = nom original
            "cheapest": cheapest,
            "second": second,
            "gap_cents": gap_cents,
            "gap_pct": gap_pct,
            "offers_count": len(items),
        })

    data.sort(key=lambda g: g["cheapest"]["price_cents"])

    return render_template("best.html", data=data, now=datetime.now(), q=q, source=source)

@app.get("/product/<gid>")
def product_details(gid: str):
    # On re-fetch puis on regroupe pareil (simple + robuste)
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT source, name, price_cents, url, image_url, scraped_at
                FROM products
                ORDER BY scraped_at DESC
                LIMIT 1000
            """)
            rows = cur.fetchall()

    groups = defaultdict(list)
    for r in rows:
        key = normalize_name(r["name"])
        groups[group_id(key)].append(r)

    items = groups.get(gid, [])
    items_sorted = sorted(items, key=lambda x: x["price_cents"]) if items else []
    cheapest = items_sorted[0] if items_sorted else None
    display_name = items_sorted[0]["name"] if items_sorted else "Produit introuvable"

    return render_template("details.html",
                           name=display_name,
                           items=items_sorted,
                           cheapest=cheapest,
                           now=datetime.now())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
