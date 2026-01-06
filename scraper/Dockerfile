FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/

# par défaut on lance le spider de test (on changera plus tard)
CMD ["bash", "-lc", "cd price_comparator && scrapy crawl test_ssd"]
