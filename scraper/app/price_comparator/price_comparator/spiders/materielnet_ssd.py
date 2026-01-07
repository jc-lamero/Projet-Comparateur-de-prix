import re
import scrapy


def parse_price_to_cents(text: str | None) -> int | None:
    """
    Ex: "179€99", "179,99 €", "1 499€95"
    Retourne un int en centimes.
    """
    if not text:
        return None
    t = text.replace("\xa0", " ").strip()

    # Cas "179€99"
    m = re.search(r"(\d[\d\s]*)\s*€\s*(\d{2})", t)
    if m:
        euros = int(m.group(1).replace(" ", ""))
        cents = int(m.group(2))
        return euros * 100 + cents

    # Cas "179,99" ou "179.99"
    m = re.search(r"(\d[\d\s]*)[,.](\d{2})", t)
    if m:
        euros = int(m.group(1).replace(" ", ""))
        cents = int(m.group(2))
        return euros * 100 + cents

    # Cas "179 €" sans centimes
    m = re.search(r"(\d[\d\s]*)\s*€", t)
    if m:
        euros = int(m.group(1).replace(" ", ""))
        return euros * 100

    return None


class MaterielNetSSDS(scrapy.Spider):
    name = "materielnet_ssd"
    allowed_domains = ["materiel.net"]
    start_urls = [
        "https://www.materiel.net/recherche/ssd/",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "AUTOTHROTTLE_ENABLED": True,
    }

    def parse(self, response):
        # ⚠️ Materiel.net peut changer ses classes.
        # On récupère les "cards" de façon assez tolérante :
        cards = response.css("article, li, div")

        found = 0

        for c in cards:
            # 1) URL produit (patterns fréquents)
            href = (
                c.css('a[href*="/produit/"]::attr(href)').get()
                or c.css('a[href*="/p/"]::attr(href)').get()
                or c.css('a[href*=".html"]::attr(href)').get()
            )
            if not href:
                continue

            url = response.urljoin(href)

            # 2) Nom : title/alt/h1 dans la card
            name = (
                c.css("a::attr(title)").get()
                or c.css("img::attr(alt)").get()
                or c.css("h2::text").get()
                or c.css("h3::text").get()
            )
            if name:
                name = " ".join(name.split())

            # 3) Prix : on prend le texte de la card et on parse
            text_blob = " ".join([t.strip() for t in c.css("::text").getall() if t.strip()])
            price_cents = parse_price_to_cents(text_blob)

            # Sans prix => pas une carte produit
            if not price_cents or not name:
                continue

            # 4) Image
            image_url = c.css("img::attr(src)").get()
            if image_url:
                image_url = response.urljoin(image_url)

            found += 1
            yield {
                "source": "materielnet",
                "name": name,
                "price_cents": price_cents,
                "url": url,
                "image_url": image_url,
            }

        # Pagination (si présente)
        next_href = (
            response.css('a[rel="next"]::attr(href)').get()
            or response.css('a.pagination__next::attr(href)').get()
            or response.css('a[aria-label*="Suivant"]::attr(href)').get()
        )
        if next_href:
            yield response.follow(next_href, callback=self.parse)

        self.logger.info("Materiel.net: produits extraits sur cette page = %s", found)
