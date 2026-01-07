import re
import scrapy

SSD_KEYWORDS = ("ssd", "nvme", "m.2", "pcie")

def extract_price_cents(container) -> int | None:
    # LDLC: "1 499€<sup>95</sup>"
    euros_txt = container.css("div.price::text").re_first(r"\d[\d\s]*€")
    if not euros_txt:
        return None
    euros = int(re.sub(r"[^\d]", "", euros_txt))
    sup = container.css("div.price sup::text").get()
    cents = int(sup.strip()) if sup and sup.strip().isdigit() else 0
    return euros * 100 + cents

class LdlcSSDSpider(scrapy.Spider):
    name = "ldlc_ssd"
    allowed_domains = ["ldlc.com"]
    start_urls = ["https://www.ldlc.com/informatique/pieces-informatique/disque-ssd/c4698/"]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "DEFAULT_REQUEST_HEADERS": {"Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"},
        "DOWNLOAD_DELAY": 1.0,
        "AUTOTHROTTLE_ENABLED": True,
    }

    def parse(self, response):
        # On part des liens produits (beaucoup plus fiable que "div.price")
        for a in response.css('a[href^="/fiche/"]'):
            href = a.attrib.get("href")
            if not href:
                continue

            # On remonte au premier ancêtre qui contient un prix
            container = a.xpath("ancestor::*[.//div[contains(@class,'price')]][1]")
            if not container:
                continue

            name = container.css("div.txt span::text").get() or container.css("img::attr(alt)").get()
            if not name:
                continue
            name = " ".join(name.split())

            # ✅ Filtre SSD sur le nom (élimine les PC)
            low = name.lower()
            if not any(k in low for k in SSD_KEYWORDS):
                continue

            price_cents = extract_price_cents(container)
            if price_cents is None:
                continue

            image_url = container.css("div.pic img::attr(src), img::attr(src)").get()
            url = response.urljoin(href)

            yield {
                "source": "ldlc",
                "name": name[:512],
                "price_cents": int(price_cents),
                "url": url,
                "image_url": image_url,
            }

        # Pagination
        next_href = response.css('a[rel="next"]::attr(href)').get()
        if next_href:
            yield response.follow(next_href, callback=self.parse)
