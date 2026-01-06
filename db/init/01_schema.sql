CREATE DATABASE IF NOT EXISTS comparateur CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE comparateur;

CREATE TABLE IF NOT EXISTS products (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  source VARCHAR(20) NOT NULL,
  name VARCHAR(512) NOT NULL,
  price_cents INT NOT NULL,
  url TEXT NOT NULL,
  image_url TEXT NULL,
  scraped_at DATETIME NOT NULL,

  UNIQUE KEY uniq_source_url (source(20), url(255)),
  INDEX idx_name (name(255)),
  INDEX idx_source (source)
);
