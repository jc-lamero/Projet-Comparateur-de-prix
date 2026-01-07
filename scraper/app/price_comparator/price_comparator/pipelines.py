import os
from datetime import datetime
import pymysql

class MySQLStorePipeline:
    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host=os.getenv("DB_HOST", "db"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "app"),
            password=os.getenv("DB_PASSWORD", "app"),
            database=os.getenv("DB_NAME", "comparateur"),
            charset="utf8mb4",
            autocommit=True,
        )
        self.cur = self.conn.cursor()

    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()

    def process_item(self, item, spider):
        scraped_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        sql = """
        INSERT INTO products (source, name, price_cents, url, image_url, scraped_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        price_cents = VALUES(price_cents),
        image_url = VALUES(image_url),
        scraped_at = NOW();
        """
        self.cur.execute(sql, (
            item["source"],
            item["name"],
            item["price_cents"],
            item["url"],
            item.get("image_url"),
))
        return item
