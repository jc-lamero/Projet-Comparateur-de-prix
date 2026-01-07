import re
import scrapy


import scrapy


class RueducommerceSSDSpider(scrapy.Spider):
    name = "rueducommerce_ssd"
    allowed_domains = ["rueducommerce.fr"]
    start_urls = [
        "https://www.rueducommerce.fr/recherche/SSD/"
    ]

    def parse(self, response):
        self.logger.info("Status: %s", response.status)
        self.logger.info("HTML size: %s", len(response.text))

        for href in response.css("a::attr(href)").getall():
            yield {
                "debug_link": href
            }


            # Filtre: on ignore les liens vides / trop courts / filtres
            if not title or len(title) < 6:
                continue
            if href.startswith("#") or href.startswith("javascript:"):
                continue
            if any(x in href for x in ("/r/", "/c/", "/login", "/panier", "/compte")):
                continue

            # On récupère un bloc parent assez large pour trouver le prix "dès"
            block = a.xpath("ancestor::*[self::article or self::li or self::div][1]")
            if not block:
                continue

            txt = " ".join(block.css("::text").getall())
            txt = re.sub(r"\s+", " ", txt).strip()

            # Prix "dès 63,51€" (on prend le premier qu’on trouve dans la carte)
            m = re.search(r"dès\s*([0-9]+(?:[.,][0-9]{1,2})?)\s*€", txt, re.IGNORECASE)
            if not m:
                # fallback: n'importe quel prix "123,45€"
                m = re.search(r"([0-9]+(?:[.,][0-9]{1,2})?)\s*€", txt)
            if not m:
                continue

            price_str = m.group(1).replace(",", ".")
            try:
                price_cents = int(round(float(price_str) * 100))
            except ValueError:
                continue

            # Image: src ou data-src selon les cas
            img = (
                block.css("img::attr(src)").get()
                or block.css("img::attr(data-src)").get()
                or block.css("img::attr(data-original)").get()
            )
            image_url = response.urljoin(img) if img else None

            url = response.urljoin(href)

            yield {
                "source": "rueducommerce",
                "name": title,
                "price_cents": price_cents,
                "url": url,
                "image_url": image_url,
            }

        # Pagination (si présent)
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
