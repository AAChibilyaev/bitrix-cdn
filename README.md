# Bitrix CDN Server

High-performance CDN server for Bitrix with automatic WebP/AVIF image conversion.

## Features

- **WebP + AVIF conversion** with 70-93% compression
- **Smart content negotiation** (AVIF → WebP → original)
- **Async processing** with 12 workers
- **Prometheus monitoring** with Grafana dashboards
- **Docker Compose** ready for production

## Quick Start

```bash
# Clone repository
git clone https://github.com/AAChibilyaev/bitrix-cdn.git
cd bitrix-cdn

# Start services
docker compose up -d

# Check status
./docker-manage.sh status
```

## Services

- **Nginx** - Web server with smart image serving
- **WebP Converter** - Async image conversion service
- **Redis** - Caching layer
- **Prometheus** - Metrics collection
- **Grafana** - Monitoring dashboards
- **AlertManager** - Alert notifications

## Management Scripts

```bash
./docker-manage.sh start    # Start all services
./docker-manage.sh stop     # Stop all services
./docker-manage.sh status   # Check service status
./docker-manage.sh logs     # View logs

./avif-ctl.sh stats        # AVIF conversion stats
./webp-ctl.sh stats        # WebP conversion stats
```

## Monitoring

- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090
- **Health Check**: http://localhost:8088/health

## Configuration

All settings in `docker-compose.yml`:

- `WEBP_QUALITY=85` - WebP quality
- `AVIF_QUALITY=80` - AVIF quality
- `WEBP_WORKER_THREADS=12` - Number of workers
- `WEBP_RATE_LIMIT=500` - Files per minute limit

## License

MIT License