import scrapy
import re
from urllib.parse import urljoin

class TopAchatSsdSpider(scrapy.Spider):
    name = "topachat_ssd"
    allowed_domains = ["topachat.com"]

    start_urls = [
        "https://www.topachat.com/pages/produits_cat_est_micro_puis_rubrique_est_w_ssd.html"
    ]

    MAX_PAGES = 4

    def parse(self, response):
        # liens produits detail2...
        product_links = response.css(
            'a[href*="detail2_cat_est_micro_puis_rubrique_est_w_ssd_puis_ref_est_"]::attr(href)'
        ).getall()

        seen = set()
        for href in product_links:
            if not href or href in seen:
                continue
            seen.add(href)

            block = response.xpath(
                f'//a[@href="{href}"]/ancestor::*[self::article or self::li or self::div][1]'
            )

            # nom
            name = (
                block.css("::text").getall()
            )
            name = " ".join([t.strip() for t in name if t.strip()])
            # heuristique: souvent le nom est dans le href card, sinon alt
            # on tente alt d'image
            alt = block.css("img::attr(alt)").get()
            if alt and len(alt.strip()) > 5:
                name = alt.strip()

            # prix (souvent 179.99)
            price_txt = block.css("::text").re_first(r"\d[\d\s]*[,.]\d{2}")
            if not price_txt:
                continue

            price_txt = price_txt.replace("\xa0", " ").strip().replace(",", ".")
            price_val = float(price_txt)
            price_cents = int(round(price_val * 100))

            image_url = block.css("img::attr(src)").get()
            if image_url and image_url.startswith("//"):
                image_url = "https:" + image_url

            yield {
                "source": "topachat",
                "name": name,
                "price_cents": price_cents,
                "url": response.urljoin(href),
                "image_url": image_url,
            }

        # --- Pagination (jusqu'à MAX_PAGES) ---
        page = response.meta.get("page", 1)
        if page >= self.MAX_PAGES:
            return

        # TopAchat : plusieurs patterns possibles pour "page suivante"
        next_href = (
            response.css('link[rel="next"]::attr(href)').get()
            or response.css('a[rel="next"]::attr(href)').get()
            or response.xpath('//a[contains(translate(., "SUIVANT", "suivant"), "suivant")]/@href').get()
            or response.xpath('//a[contains(@aria-label, "Suivant")]/@href').get()
        )

        if next_href:
            next_url = urljoin(response.url, next_href)
            yield scrapy.Request(next_url, callback=self.parse, meta={"page": page + 1})
