BOT_NAME = "price_comparator"

SPIDER_MODULES = ["price_comparator.spiders"]
NEWSPIDER_MODULE = "price_comparator.spiders"

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1.0
AUTOTHROTTLE_ENABLED = True

ITEM_PIPELINES = {
    "price_comparator.pipelines.MySQLStorePipeline": 300,
}
