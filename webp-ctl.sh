#!/bin/bash
# WebP Converter Management Script

CONTAINER_NAME="cdn-webp-converter"
COMPOSE_FILE="docker-compose.yml"

case "$1" in
    start)
        echo "Starting WebP Converter..."
        docker compose -f $COMPOSE_FILE up -d webp-converter-async
        ;;
    stop)
        echo "Stopping WebP Converter..."
        docker compose -f $COMPOSE_FILE stop webp-converter-async
        ;;
    restart)
        echo "Restarting WebP Converter..."
        docker compose -f $COMPOSE_FILE restart webp-converter-async
        ;;
    logs)
        docker compose -f $COMPOSE_FILE logs -f webp-converter-async
        ;;
    stats)
        echo "=== WebP Converter Statistics ==="
        curl -s http://localhost:9101/metrics | grep webp_
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
        echo "Building WebP Converter..."
        docker compose -f $COMPOSE_FILE build webp-converter-async
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|stats|health|ready|rescan|exec|build}"
        exit 1
        ;;
esac
