import scrapy

class TestSSDSpider(scrapy.Spider):
    name = "test_ssd"
    start_urls = ["https://example.com/"]

    def parse(self, response):
        yield {
            "source": "darty",
            "name": "SSD Samsung 1TB (TEST)",
            "price_cents": 7999,
            "url": "https://example.com/darty-ssd-1tb",
            "image_url": None,
        }
        yield {
            "source": "cdiscount",
            "name": "SSD Samsung 1TB (TEST)",
            "price_cents": 7499,
            "url": "https://example.com/cdiscount-ssd-1tb",
            "image_url": None,
        }
