# 🚀 Deployment Guide

## Production Deployment Checklist

### 1. Environment Configuration

```bash
# Copy and configure environment variables
cp .env.example .env

# Set production values:
# - SECRET_KEY: Generate secure random key
# - DATABASE_URL: Production database
# - API keys for exchanges
# - ENVIRONMENT=production
# - DEBUG=false
```

### 2. Database Setup

```bash
# Run with Docker Compose
docker-compose up -d postgres

# Initialize TimescaleDB
docker exec -it trading_postgres psql -U trading_user -d trading_db -f /docker-entrypoint-initdb.d/init.sql

# Run migrations
cd backend
alembic upgrade head
```

### 3. Build & Deploy with Docker

```bash
# Build all services
docker-compose build

# Start in production mode
docker-compose up -d

# Check logs
docker-compose logs -f

# Scale workers if needed
docker-compose up -d --scale celery_worker=4
```

### 4. SSL/HTTPS Setup

For production, use Nginx with Let's Encrypt:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 5. Monitoring Setup

**Prometheus + Grafana:**

```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml

grafana:
  image: grafana/grafana
  ports:
    - "3001:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
```

**Sentry Error Tracking:**

```python
# In backend/main.py
import sentry_sdk
sentry_sdk.init(dsn=settings.SENTRY_DSN)
```

### 6. Backup Strategy

```bash
# Database backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec trading_postgres pg_dump -U trading_user trading_db > backup_$DATE.sql
```

### 7. Security Hardening

- [ ] Change all default passwords
- [ ] Enable firewall (only 80, 443, 22)
- [ ] Setup fail2ban
- [ ] Enable 2FA for admin accounts
- [ ] Regular security updates
- [ ] API rate limiting enabled
- [ ] CORS properly configured

### 8. Performance Optimization

```python
# Backend optimizations
- Enable database connection pooling
- Use Redis for caching
- Celery worker auto-scaling
- CDN for static files

# Frontend optimizations
- Build with production mode
- Enable gzip compression
- Lazy loading for routes
- Image optimization
```

### 9. Scaling Guidelines

**Horizontal Scaling:**

```bash
# Scale API servers
docker-compose up -d --scale api=3

# Scale Celery workers
docker-compose up -d --scale celery_worker=5
```

**Database Scaling:**

- Use TimescaleDB compression
- Regular VACUUM and ANALYZE
- Connection pooling (PgBouncer)
- Read replicas for analytics

### 10. Health Checks

```bash
# API health
curl https://yourdomain.com/health

# Database connection
curl https://yourdomain.com/api/v1/status

# Celery workers
docker exec trading_celery_worker celery -A tasks inspect active
```

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | JWT secret key | `your-secret-key-here` |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `BINANCE_API_KEY` | Binance API key | `your-api-key` |
| `BINANCE_API_SECRET` | Binance API secret | `your-api-secret` |
| `SENTRY_DSN` | Sentry error tracking | `https://...` |

## Troubleshooting

### Issue: Database connection failed
```bash
# Check database is running
docker ps | grep postgres

# Check logs
docker logs trading_postgres

# Test connection
docker exec trading_postgres psql -U trading_user -d trading_db -c "SELECT 1"
```

### Issue: Celery tasks not running
```bash
# Check workers
docker logs trading_celery_worker

# Restart workers
docker-compose restart celery_worker celery_beat
```

### Issue: High memory usage
```bash
# Check resource usage
docker stats

# Adjust worker concurrency
# In docker-compose.yml:
command: celery -A tasks worker --loglevel=info --concurrency=2
```

## Maintenance

### Weekly Tasks
- Review error logs
- Check disk space
- Backup database
- Update dependencies

### Monthly Tasks
- Security patches
- Performance review
- Cost optimization
- Model retraining

### Quarterly Tasks
- Full system audit
- Load testing
- Disaster recovery drill
- Documentation update
