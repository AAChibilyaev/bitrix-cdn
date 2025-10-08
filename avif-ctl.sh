#!/bin/bash
# AVIF Converter Management Script

CONTAINER_NAME="cdn-webp-converter-async"
COMPOSE_FILE="docker-compose.yml"

case "$1" in
    start)
        echo "Starting AVIF Converter..."
        docker compose -f $COMPOSE_FILE up -d webp-converter-async
        ;;
    stop)
        echo "Stopping AVIF Converter..."
        docker compose -f $COMPOSE_FILE stop webp-converter-async
        ;;
    restart)
        echo "Restarting AVIF Converter..."
        docker compose -f $COMPOSE_FILE restart webp-converter-async
        ;;
    logs)
        docker compose -f $COMPOSE_FILE logs -f webp-converter-async
        ;;
    stats)
        echo "=== AVIF Converter Statistics ==="
        curl -s http://localhost:9101/metrics | grep -E "(webp_|avif_)"
        ;;
    health)
        echo "=== Health Check ==="
        curl -s http://localhost:8088/health | jq .
        ;;
    ready)
        echo "=== Readiness Check ==="
        curl -s http://localhost:8088/ready | jq .
        ;;
    rescan)
        echo "Triggering rescan..."
        docker exec $CONTAINER_NAME kill -HUP 1
        ;;
    exec)
        docker exec -it $CONTAINER_NAME /bin/bash
        ;;
    build)
        echo "Building AVIF Converter..."
        docker compose -f $COMPOSE_FILE build webp-converter-async
        ;;
    test-avif)
        echo "Testing AVIF conversion..."
        docker exec $CONTAINER_NAME python -c "
import asyncio
from pathlib import Path
from PIL import Image
import tempfile
import os

async def test_avif():
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        # Create test image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(tmp.name, 'JPEG')
        
        avif_path = tmp.name.replace('.jpg', '.avif')
        
        # Convert to AVIF
        with Image.open(tmp.name) as img:
            img.save(avif_path, 'AVIF', quality=80)
        
        print(f'AVIF conversion test: {os.path.exists(avif_path)}')
        print(f'Original size: {os.path.getsize(tmp.name)} bytes')
        print(f'AVIF size: {os.path.getsize(avif_path)} bytes')
        
        # Cleanup
        os.unlink(tmp.name)
        os.unlink(avif_path)

asyncio.run(test_avif())
"
        ;;
    enable-avif)
        echo "Enabling AVIF conversion..."
        docker exec $CONTAINER_NAME sh -c "echo 'ENABLE_AVIF=true' >> /app/.env"
        docker restart $CONTAINER_NAME
        ;;
    disable-avif)
        echo "Disabling AVIF conversion..."
        docker exec $CONTAINER_NAME sh -c "echo 'ENABLE_AVIF=false' >> /app/.env"
        docker restart $CONTAINER_NAME
        ;;
    enable-webp)
        echo "Enabling WebP conversion..."
        docker exec $CONTAINER_NAME sh -c "echo 'ENABLE_WEBP=true' >> /app/.env"
        docker restart $CONTAINER_NAME
        ;;
    disable-webp)
        echo "Disabling WebP conversion..."
        docker exec $CONTAINER_NAME sh -c "echo 'ENABLE_WEBP=false' >> /app/.env"
        docker restart $CONTAINER_NAME
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|stats|health|ready|rescan|exec|build|test-avif|enable-avif|disable-avif|enable-webp|disable-webp}"
        echo ""
        echo "Commands:"
        echo "  start         - Start the converter service"
        echo "  stop          - Stop the converter service"
        echo "  restart       - Restart the converter service"
        echo "  logs          - Show service logs"
        echo "  stats         - Show conversion statistics"
        echo "  health        - Health check"
        echo "  ready         - Readiness check"
        echo "  rescan        - Trigger directory rescan"
        echo "  exec          - Open shell in container"
        echo "  build         - Build Docker image"
        echo "  test-avif     - Test AVIF conversion"
        echo "  enable-avif   - Enable AVIF conversion"
        echo "  disable-avif  - Disable AVIF conversion"
        echo "  enable-webp   - Enable WebP conversion"
        echo "  disable-webp  - Disable WebP conversion"
        exit 1
        ;;
esac
