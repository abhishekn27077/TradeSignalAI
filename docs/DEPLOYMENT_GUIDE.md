# TradeSignalAI-v3 — Deployment Guide

This guide covers production deployment using Docker Compose, Nginx reverse proxying, and environment hardening.

---

## 1. Prerequisites

- Linux Server (Ubuntu 22.04 LTS recommended)
- Docker Engine 24.0+ and Docker Compose v2+
- Domain name pointed to your server IP (for SSL setup)

---

## 2. Production Docker Deployment

### Step 1: Clone Repository & Create `.env`
```bash
git clone https://github.com/your-org/TradeSignalAI-v3.git
cd TradeSignalAI-v3
cp .env.example .env
```

### Step 2: Configure Environment Variables
Edit `.env` to configure production secrets:
```env
ENVIRONMENT=production
EXECUTION_MODE=DEMO
SECRET_KEY=generate_a_secure_random_string_here
POSTGRES_PASSWORD=your_strong_db_password
REDIS_PASSWORD=your_strong_redis_password
OMNIROUTE_BASE_URL=http://omniroute-gateway:20128/v1
```

### Step 3: Build & Launch Services
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## 3. SSL / HTTPS Setup with Certbot

To attach SSL certificates to the Nginx reverse proxy:
```bash
sudo apt-get update && sudo apt-get install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

---

## 4. Monitoring & Health Status

Check service logs:
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
```

Query the API health endpoint:
```bash
curl http://localhost/api/v1/health
curl http://localhost/api/v1/status
```
