# 🚀 KOMPAGNON Deployment Guide

Complete guide for deploying KOMPAGNON Automation System to production (VPS, Heroku, AWS, etc.)

---

## 📋 Prerequisites

- Linux VPS (Ubuntu 20.04 LTS recommended)
- Python 3.10+
- Node.js 18+ (for frontend)
- PostgreSQL 13+ (or stick with SQLite for MVP)
- SSL Certificate (Let's Encrypt, free)
- Domain name

---

## 🏪 Option 1: VPS Deployment (DigitalOcean, Linode, Vultr)

### 1. Server Setup

```bash
# SSH into server
ssh root@your.server.ip

# Update system
apt update && apt upgrade -y
apt install -y python3.10 python3-pip python3-venv nodejs npm postgresql

# Create app user
useradd -m -s /bin/bash kompagnon
su - kompagnon
```

### 2. Clone & Install Backend

```bash
cd /home/kompagnon
git clone https://github.com/your-org/kompagnon.git
cd kompagnon

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
nano .env  # Edit with your API keys and settings
```

### 3. Setup PostgreSQL Database

```bash
sudo -u postgres psql

CREATE DATABASE kompagnon_db;
CREATE USER kompagnon_user WITH PASSWORD 'secure_password_here';
ALTER ROLE kompagnon_user SET client_encoding TO 'utf8';
ALTER ROLE kompagnon_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE kompagnon_user SET default_transaction_deferrable TO on;
ALTER ROLE kompagnon_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE kompagnon_db TO kompagnon_user;
\q
```

Update `.env`:
```
DATABASE_URL=postgresql://kompagnon_user:secure_password_here@localhost/kompagnon_db
```

### 4. Initialize Database

```bash
cd /home/kompagnon/kompagnon/backend
python3 -c "
from database import init_db
from seed_checklists import seed_checklists
init_db()
seed_checklists()
print('✓ Database initialized and seeded')
"
```

### 5. Setup Backend Service (Gunicorn + Supervisor)

```bash
# Install Gunicorn
pip install gunicorn

# Create supervisor config
sudo nano /etc/supervisor/conf.d/kompagnon-backend.conf
```

```ini
[program:kompagnon-backend]
directory=/home/kompagnon/kompagnon/backend
command=/home/kompagnon/kompagnon/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 main:app
user=kompagnon
autostart=true
autorestart=true
stderr_logfile=/var/log/kompagnon-backend.log
stdout_logfile=/var/log/kompagnon-backend.log
environment=PATH="/home/kompagnon/kompagnon/venv/bin",ENVIRONMENT="production"
```

### 6. Setup Frontend

```bash
cd /home/kompagnon/kompagnon/frontend
npm install
REACT_APP_API_URL=https://api.youromain.de npm run build

# Serve with Nginx (see step 8)
```

### 7. Setup Nginx Reverse Proxy

```bash
sudo apt install -y nginx
sudo nano /etc/nginx/sites-available/kompagnon
```

```nginx
upstream kompagnon_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.de api.yourdomain.de;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.de;

    # SSL Certificates (from Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.de/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;

    # Frontend
    root /home/kompagnon/kompagnon/frontend/build;
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API Proxy
    location /api {
        proxy_pass http://kompagnon_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 10M;
    }
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.de;

    ssl_certificate /etc/letsencrypt/live/yourdomain.de/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.de/privkey.pem;

    location / {
        proxy_pass http://kompagnon_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and start:
```bash
sudo ln -s /etc/nginx/sites-available/kompagnon /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. SSL Certificate with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot certonly --standalone -d yourdomain.de -d api.yourdomain.de
```

### 9. Start Services

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start kompagnon-backend

# Check status
sudo supervisorctl status kompagnon-backend
```

### 10. Verify Deployment

```bash
# Test API
curl https://api.yourdomain.de/health

# Check logs
tail -f /var/log/kompagnon-backend.log

# Monitor with
top
```

---

## 🐳 Option 2: Docker Deployment

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: kompagnon_db
      POSTGRES_USER: kompagnon_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://kompagnon_user:${DB_PASSWORD}@db/kompagnon_db
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    depends_on:
      - db
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: https://api.yourdomain.de
    restart: unless-stopped

volumes:
  postgres_data:
```

Deploy:
```bash
docker-compose -f docker-compose.yml up -d
```

---

## ☁️ Option 3: Heroku Deployment

### Procfile (backend)
```
web: gunicorn -w 4 main:app
release: python3 -c "from database import init_db; from seed_checklists import seed_checklists; init_db(); seed_checklists()"
```

### Deploy
```bash
heroku login
heroku create kompagnon
heroku addons:create heroku-postgresql:standard-0

git push heroku main

heroku open
```

---

## ⚙️ Post-Deployment Configuration

### 1. Setup Email

For Gmail SMTP:
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
FROM_EMAIL=noreply@yourdomain.de
```

Generate App Password: https://myaccount.google.com/apppasswords

### 2. Configure API Keys

```bash
# .env on production server
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_PAGESPEED_API_KEY=AIza...
export SMTP_PASSWORD=...
```

### 3. Setup Monitoring

```bash
# Install and configure PM2 for process monitoring
npm install -g pm2
pm2 start /path/to/gunicorn -- -w 4 -b 0.0.0.0:8000 main:app
pm2 save
```

### 4. Backup Strategy

```bash
# Daily database backup
0 2 * * * pg_dump kompagnon_db | gzip > /backups/kompagnon_$(date +\%Y\%m\%d).sql.gz

# Keep last 30 days
find /backups -name "kompagnon_*.sql.gz" -mtime +30 -delete
```

---

## 🔒 Security Checklist

- [ ] SSL certificate installed and auto-renewal configured
- [ ] Firewall configured (ufw):
  ```bash
  sudo ufw default deny incoming
  sudo ufw allow 22/tcp
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```
- [ ] API keys in `.env` (never in code)
- [ ] Database password strong & unique
- [ ] CORS origins restricted
- [ ] Rate limiting configured
- [ ] Database backups automated
- [ ] Log monitoring enabled
- [ ] Fail2Ban installed for brute-force protection

---

## 📊 Monitoring & Logging

```bash
# View logs in real-time
tail -f /var/log/kompagnon-backend.log
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Monitor with Prometheus + Grafana
# Or use: DataDog, New Relic, Sentry
```

---

## 🔄 CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy KOMPAGNON

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.VPS_HOST }}
          username: kompagnon
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd kompagnon
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            supervisorctl restart kompagnon-backend
```

---

## 📞 Support & Troubleshooting

### Backend won't start
```bash
# Check Python version
python3 --version

# Check dependencies
pip list

# Test database connection
psql postgresql://user:pass@localhost/kompagnon_db
```

### API returns 502 (Bad Gateway)
```bash
# Check if backend is running
sudo supervisorctl status kompagnon-backend

# Check error logs
tail -100 /var/log/kompagnon-backend.log

# Restart
sudo supervisorctl restart kompagnon-backend
```

### Scheduler not running
```bash
# Backend logs show scheduler errors
# Likely missing APScheduler database table
# Recreate database tables:
python3 -c "from database import init_db; init_db()"
```

---

## 🎉 You're Live!

Once deployed:

1. **Health Check**: https://yourdomain.de/health → should return `{"status": "ok"}`
2. **API Docs**: https://api.yourdomain.de/docs (Swagger UI)
3. **Frontend**: https://yourdomain.de
4. **Monitor**: Check logs regularly, set up alerts

---

**Next**: Set up automated backups, monitoring, and enable Analytics (Google Analytics, Sentry)
