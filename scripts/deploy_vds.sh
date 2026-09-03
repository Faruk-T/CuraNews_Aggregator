#!/usr/bin/env bash
# ==============================================================================
# CuraNews VDS Production Deployment Script (Day 23)
# Automatic Setup: Docker, Caddy, Auto-SSL, PostgreSQL, Redis, FastAPI, Alembic
# ==============================================================================

set -euo pipefail

echo "=========================================================="
echo " 🚀 CuraNews VDS Canlı Dağıtım Otomasyonu Başlatılıyor..."
echo "=========================================================="

# 1. Check Docker & Compose
if ! command -v docker &> /dev/null; then
    echo "⚠️ Docker kurulu değil. Ubuntu paket yöneticisiyle kuruluyor..."
    sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
    sudo systemctl enable --now docker
fi

# 2. Check environment file
if [ ! -f ".env.production" ]; then
    echo "📄 .env.production oluşturuluyor..."
    cp .env.example .env.production || true
fi

# 3. Pull & Build
echo "📦 Docker konteynerleri inşa ediliyor (Multi-stage build)..."
docker compose -f docker-compose.prod.yml build

# 4. Start Stack
echo "🌐 Servisler ayağa kaldırılıyor (Postgres, Redis, API, Caddy SSL)..."
docker compose -f docker-compose.prod.yml up -d

# 5. Run Database Migrations
echo "🗄️ Veritabanı migrasyonları uygulanıyor (Alembic upgrade head)..."
docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head

# 6. Status check
echo "🔍 Sağlık kontrolleri yapılıyor..."
sleep 5
docker compose -f docker-compose.prod.yml ps

echo "=========================================================="
echo " 🎉 CuraNews Canlı Dağıtımı Başarıyla Tamamlandı!"
echo " 🌐 Web Arayüzü: http://localhost veya https://\${DOMAIN_NAME:-curanews.com}"
echo " 📑 Site Haritası: /sitemap.xml"
echo " 🤖 Robots.txt: /robots.txt"
echo " 📢 ads.txt: /ads.txt"
echo " 📡 RSS Akışı: /rss.xml"
echo "=========================================================="
