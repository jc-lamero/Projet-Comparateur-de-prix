import re
import scrapy

PRODUCT_LINK_SUBSTR = "detail2_cat_est_micro_puis_rubrique_est_w_ssd_puis_ref_est_"

def extract_price_cents(block) -> int | None:
    # TopAchat: on a vu un texte du type "179.99"
    # On récupère un float-like "xxx.xx" ou "xxx,xx"
    txts = block.css("::text").getall()
    joined = " ".join(t.strip() for t in txts if t and t.strip())

    m = re.search(r"(\d[\d\s]*)([.,])(\d{2})", joined)
    if not m:
        return None

    euros = int(re.sub(r"[^\d]", "", m.group(1)))
    cents = int(m.group(3))
    return euros * 100 + cents

class TopAchatSSDSpider(scrapy.Spider):
    name = "topachat_ssd"
    allowed_domains = ["topachat.com"]
    start_urls = ["https://www.topachat.com/pages/produits_cat_est_micro_puis_rubrique_est_w_ssd.html"]

    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "DEFAULT_REQUEST_HEADERS": {
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
        "DOWNLOAD_DELAY": 1.0,
        "AUTOTHROTTLE_ENABLED": True,
    }

    def parse(self, response):
        links = response.css(f'a[href*="{PRODUCT_LINK_SUBSTR}"]')
        for a in links:
            href = a.attrib.get("href")
            if not href:
                continue

            # bloc produit
            block = a.xpath("ancestor::div[contains(@class,'product-list__product-wrapper')][1]")
            if not block:
                block = a.xpath("ancestor::*[self::article or self::li or self::div][1]")

            # nom (dans le bloc, souvent un texte de titre / nom produit)
            name = block.css("h3::text, h2::text, .product__title::text, .product__name::text").get()
            if not name:
                # fallback : alt image
                name = block.css("img::attr(alt)").get()

            if not name:
                # dernier fallback : texte du lien
                name = " ".join(a.css("::text").getall()).strip()

            name = " ".join((name or "").split())
            if not name:
                continue

            price_cents = extract_price_cents(block)
            if price_cents is None:
                continue

            image_url = block.css("img::attr(src)").get()
            url = response.urljoin(href)

            yield {
                "source": "topachat",
                "name": name[:512],
                "price_cents": int(price_cents),
                "url": url,
                "image_url": image_url,
            }

        # Pagination (TopAchat utilise souvent ?page=2 ou un paramètre "p="
        # On cherche un lien "page suivante" si présent
        next_href = response.css('a[rel="next"]::attr(href)').get()
        if not next_href:
            next_href = response.css('a.pagination__next::attr(href), a.next::attr(href)').get()

        if next_href:
            yield response.follow(next_href, callback=self.parse)
