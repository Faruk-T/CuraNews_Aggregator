# CuraNews — Canlı Dağıtım (Production VDS & Domain) ve SEO Kılavuzu

Bu doküman; CuraNews platformunun canlı bir **domain** ve **VDS (Sanal Sunucu)** üzerinde yüksek erişilebilirlik, otomatik SSL sertifikasyonu, Google Analytics 4 ve Google Search Console indeksleme standartlarıyla nasıl yayıma alınacağını adım adım açıklar.

---

## 🏗️ 1. Sistem ve Dağıtım Mimarisi

```
[ İnternet / Mobil & Web Okurları ]
                 │
                 ▼ (HTTP :80 / HTTPS :443)
┌─────────────────────────────────────────────────────────────┐
│ Caddy Web Server (Ters Proxy & Otomatik Let's Encrypt SSL)  │
│  - Otomatik HTTP -> HTTPS yönlendirmesi                     │
│  - zstd / gzip sıkıştırma                                   │
│  - Güvenlik Başlıkları (HSTS, CSP, X-Frame-Options)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ (Dahili Ağ)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ CuraNews API (FastAPI + Uvicorn)                            │
│  - REST API & Canlı Web UI (/ui/)                           │
│  - Dinamik SEO (/sitemap.xml, /robots.txt, /rss.xml)        │
│  - IAB Reklam Doğrulama (/ads.txt)                          │
│  - Kriptografik Kimlik Doğrulama & Oturum                   │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
 ┌───────────────────────────┐   ┌───────────────────────────┐
 │ PostgreSQL 16 (Veritabanı)│   │ Redis 7 (Önbellek & Kuyruk)│
 │  - Kalıcı Veri Hacmi      │   │  - Feed Caching (TTL)     │
 └───────────────────────────┘   └───────────────────────────┘
```

---

## 🌐 2. Domain & DNS Yapılandırması

Bir domain (alan adı) satın aldığınızda (Natro, İsimTescil, GoDaddy, Cloudflare, Namecheap vb.), DNS yönetim panelinde aşağıdaki kayıtları oluşturun:

| Kayıt Tipi | Ad (Name / Host) | Değer (IP Adresi) | Açıklama |
| :--- | :--- | :--- | :--- |
| **A** | `@` (veya root) | `VDS_SUNUCU_IP_ADRESI` | Ana domain yönlendirmesi (`curanews.com`) |
| **A** | `www` | `VDS_SUNUCU_IP_ADRESI` | www alt alan adı yönlendirmesi (`www.curanews.com`) |

> [!TIP]
> Caddy Web Server, `Caddyfile` içindeki `{$DOMAIN_NAME}` değişkenine tanımlanan alan adını algılayarak Let's Encrypt üzerinden otomatik olarak ücretsiz SSL/TLS sertifikasını 30 saniye içinde alır ve 90 günde bir otomatik olarak yeniler.

---

## 💻 3. VDS Sunucu Hazırlığı (Ubuntu / Debian)

Herhangi bir bulut sağlayıcıdan (DigitalOcean Droplet, Hetzner Cloud, AWS EC2, Contabo vb.) 1 vCPU - 2GB RAM özelliklerinde bir Linux sunucu açtıktan sonra:

```bash
# 1. Sunucuya SSH ile bağlanın
ssh root@SUNUCU_IP_ADRESI

# 2. Paketleri güncelleyin ve Git & Docker kurun
sudo apt-get update && sudo apt-get install -y git curl docker.io docker-compose-plugin
sudo systemctl enable --now docker

# 3. Güvenlik Duvarını (UFW) Yapılandırın
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

---

## 🚀 4. Projeyi Klonlama ve Tek Komutla Yayına Alma

```bash
# 1. Depoyu klonlayın
git clone https://github.com/Faruk-T/CuraNews_Aggregator.git
cd CuraNews_Aggregator

# 2. Ortam değişkenlerini düzenleyin
cp .env.production .env
nano .env # DOMAIN_NAME=sizindomaininiz.com olarak güncelleyin

# 3. Dağıtım Otomasyonunu Çalıştırın
chmod +x scripts/deploy_vds.sh
./scripts/deploy_vds.sh
```

Bu script sırasıyla:
1. Docker konteynerlerini optimize multi-stage build ile inşa eder.
2. PostgreSQL, Redis, CuraNews API ve Caddy servislerini başlatır.
3. `alembic upgrade head` ile veritabanı şemalarını otomatik uygular.
4. İlk haberleri ve kaynakları bootstrap ile indirip akışı hazır hale getirir.

---

## 📈 5. Google Search Console & Google Analytics 4 (GA4) Kurulumu

### Google Search Console:
1. [Google Search Console](https://search.google.com/search-console) paneline giriş yapın.
2. "URL ön eki" seçeneğine domain adresinizi (`https://sizindomaininiz.com`) yazın.
3. Doğrulama yöntemi olarak **"HTML Etiketi"** seçeneğindeki kodu kopyalayıp `.env` dosyasındaki `GSC_VERIFICATION_TOKEN` alanına yapıştırın.
4. Sol menüden **"Site Haritaları (Sitemaps)"** sekmesine giderek `https://sizindomaininiz.com/sitemap.xml` adresini gönderin.

### Google Analytics 4:
1. [Google Analytics](https://analytics.google.com/) panelinde yeni bir GA4 mülkü ve "Web Veri Akışı" oluşturun.
2. Size verilen `G-XXXXXXXXXX` formatındaki Ölçüm Kimliğini `.env` içindeki `GA_MEASUREMENT_ID` alanına kaydedin.
3. CuraNews arayüzü; sayfa görüntülemelerini, okunan haber kategorilerini, arama terimlerini ve favori etkileşimlerini otomatik olarak GA4 paneline aktaracaktır.

---

## 📢 6. Google AdSense & IAB Reklam Uyumluluğu

- **`ads.txt` Doğrulaması:** Google AdSense hesabınızdaki yayıncı numaranızı (`pub-XXXXXXXXXXXXXXXX`) `.env` dosyasında `ADSENSE_PUB_ID` değişkenine yazdığınızda, `https://sizindomaininiz.com/ads.txt` üzerinden anında doğrulanır.
- **Çerez Onayı (Cookie Consent):** Sitede yer alan açılır çerez çubuğu, IAB TCF ve KVKK standartlarına uygun olarak okuyucudan izin almadan takip çerezlerini çalıştırmaz.
- **Şeffaf Sponsorluk:** Tüm reklam alanları `SPONSORLU` etiketi taşır.
