import scrapy
import re
from urllib.parse import urljoin

class LdlcSsdSpider(scrapy.Spider):
    name = "ldlc_ssd"
    allowed_domains = ["ldlc.com"]

    # Page catégorie SSD LDLC (celle qui marche chez toi)
    start_urls = [
        "https://www.ldlc.com/informatique/pieces-informatique/disque-ssd/c4698/"
    ]

    MAX_PAGES = 5

    def parse(self, response):
        # --- Extraction produits ---
        # on prend chaque bloc parent autour d'un lien /fiche/
        for a in response.css('a[href^="/fiche/"]'):
            href = a.attrib.get("href")
            if not href:
                continue

            block = a.xpath("ancestor::*[self::div or self::li][1]")

            name = (
                block.css("div.txt span::text").get()
                or block.css("img::attr(alt)").get()
                or a.css("::text").get()
                or ""
            )
            name = name.strip()

            # prix: ex "1 499€" + sup "95"
            euros_txt = block.css("div.price::text").get() or ""
            euros_txt = euros_txt.replace("\xa0", " ").strip()
            euros_digits = re.sub(r"[^\d]", "", euros_txt)

            cents_sup = block.css("div.price sup::text").get() or "00"
            cents_digits = re.sub(r"[^\d]", "", cents_sup).zfill(2)[:2]

            if not euros_digits:
                continue

            price_cents = int(euros_digits) * 100 + int(cents_digits)

            image_url = block.css("img::attr(src)").get()
            if image_url and image_url.startswith("//"):
                image_url = "https:" + image_url

            yield {
                "source": "ldlc",
                "name": name,
                "price_cents": price_cents,
                "url": response.urljoin(href),
                "image_url": image_url,
            }

        # --- Pagination (jusqu'à MAX_PAGES) ---
        page = response.meta.get("page", 1)

        if page >= self.MAX_PAGES:
            return

        # LDLC donne souvent un link rel=next (robuste)
        next_href = (
            response.css('link[rel="next"]::attr(href)').get()
            or response.css('a[rel="next"]::attr(href)').get()
            or response.xpath('//a[contains(., "Suivant")]/@href').get()
        )

        if next_href:
            next_url = urljoin(response.url, next_href)
            yield scrapy.Request(next_url, callback=self.parse, meta={"page": page + 1})
