# 🚀 Bitrix CDN Server

> **Enterprise-grade CDN solution** with automatic WebP/AVIF conversion for Bitrix CMS

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker)](https://www.docker.com/)
[![WebP](https://img.shields.io/badge/WebP-Optimized-FF6B6B?style=flat&logo=webp)](https://developers.google.com/speed/webp)
[![AVIF](https://img.shields.io/badge/AVIF-Supported-00D4AA?style=flat&logo=avif)](https://avif.io/)
[![Monitoring](https://img.shields.io/badge/Monitoring-Grafana-F46800?style=flat&logo=grafana)](https://grafana.com/)

## ⚡ Performance Boost

- **70-93% smaller images** with WebP/AVIF conversion
- **3x faster page loads** with smart content negotiation
- **12 async workers** processing 500+ images/minute
- **Real-time monitoring** with Prometheus + Grafana

## 🎯 Smart Image Serving

```nginx
# Intelligent content negotiation
AVIF (best) → WebP (good) → Original (fallback)
```

- **AVIF**: 80% quality, maximum compression
- **WebP**: 85% quality, wide browser support  
- **Smart detection**: Automatic format selection by browser
- **Caching**: 1-year cache with immutable headers

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Bitrix CMS    │───▶│   SSHFS Mount   │───▶│  CDN Server     │
│   (Original)    │    │   (Remote)      │    │  (Optimized)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                       ┌───────────────────────────────▼───────────────────────────────┐
                       │                    CDN Services                                │
                       │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
                       │  │    Nginx     │  │  Converter  │  │    Monitoring       │  │
                       │  │  (Serving)   │  │ (WebP/AVIF) │  │ (Prometheus/Grafana)│  │
                       │  └─────────────┘  └─────────────┘  └─────────────────────┘  │
                       └───────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
# 1. Clone repository
git clone https://github.com/AAChibilyaev/bitrix-cdn.git
cd bitrix-cdn

# 2. Start all services
docker compose up -d

# 3. Check status
./docker-manage.sh status

# 4. View monitoring
open http://localhost:3000  # Grafana
```

## 📊 Real-time Monitoring

| Service | URL | Purpose |
|---------|-----|---------|
| **Grafana** | http://localhost:3000 | Performance dashboards |
| **Prometheus** | http://localhost:9090 | Metrics collection |
| **Health Check** | http://localhost:8088/health | Service status |

## 🛠️ Management Commands

```bash
# Service management
./docker-manage.sh start     # Start all services
./docker-manage.sh stop      # Stop all services
./docker-manage.sh restart   # Restart all services
./docker-manage.sh status    # Check service status
./docker-manage.sh logs      # View all logs

# Image conversion
./webp-ctl.sh stats         # WebP conversion statistics
./avif-ctl.sh stats         # AVIF conversion statistics
./webp-ctl.sh rescan        # Trigger directory rescan
```

## ⚙️ Configuration

### Image Quality Settings
```yaml
# docker-compose.yml
WEBP_QUALITY=85          # WebP quality (1-100)
AVIF_QUALITY=80          # AVIF quality (1-100)
WEBP_WORKER_THREADS=12   # Async workers
WEBP_RATE_LIMIT=500      # Files per minute
```

### Supported Formats
- **Input**: JPG, JPEG, PNG, GIF, BMP
- **Output**: WebP, AVIF
- **Min Size**: 10KB (configurable)

## 🔧 Production Features

### High Availability
- **Health checks** for all services
- **Auto-restart** on failure
- **Read-only containers** for security
- **Resource limits** and monitoring

### Security
- **No new privileges** security option
- **Read-only filesystem** for containers
- **Rate limiting** (100 req/sec per IP)
- **CORS headers** for cross-origin requests

### Performance
- **Async processing** with 12 workers
- **Queue management** (10,000 items max)
- **Batch processing** (50 files per batch)
- **Smart caching** with immutable headers

## 📈 Monitoring Dashboards

- **CDN Performance**: Request rates, response times, cache hit ratios
- **Image Conversion**: WebP/AVIF conversion statistics
- **System Health**: CPU, memory, disk usage
- **Alerts**: Automatic notifications for issues

## 🎯 Use Cases

- **E-commerce**: Faster product image loading
- **News sites**: Optimized article images
- **Corporate sites**: Reduced bandwidth costs
- **High-traffic**: Scalable image delivery

## 📋 Requirements

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **4GB RAM** minimum
- **10GB disk** for image cache

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

**Made with ❤️ by [AAChibilyaev](https://github.com/AAChibilyaev)**