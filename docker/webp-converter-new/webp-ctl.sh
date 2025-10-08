#!/bin/bash
# WebP Converter Service Control Script

SERVICE_NAME="webp-converter"
COMPOSE_FILE="docker-compose.test.yml"

case "$1" in
    start)
        echo "Starting WebP Converter service..."
        docker-compose -f $COMPOSE_FILE up -d $SERVICE_NAME
        echo "Service started. Check logs with: $0 logs"
        ;;
    stop)
        echo "Stopping WebP Converter service..."
        docker-compose -f $COMPOSE_FILE down
        echo "Service stopped."
        ;;
    restart)
        echo "Restarting WebP Converter service..."
        docker-compose -f $COMPOSE_FILE restart $SERVICE_NAME
        echo "Service restarted."
        ;;
    logs)
        echo "Showing WebP Converter logs..."
        docker-compose -f $COMPOSE_FILE logs -f $SERVICE_NAME
        ;;
    stats)
        echo "WebP Converter statistics:"
        echo "Health check:"
        curl -s http://localhost:8088/health | jq . 2>/dev/null || curl -s http://localhost:8088/health
        echo -e "\nReadiness check:"
        curl -s http://localhost:8088/ready | jq . 2>/dev/null || curl -s http://localhost:8088/ready
        echo -e "\nQueue status:"
        curl -s http://localhost:9101/queue/status | jq . 2>/dev/null || curl -s http://localhost:9101/queue/status
        echo -e "\nMetrics (first 10 lines):"
        curl -s http://localhost:9101/metrics | head -10
        ;;
    health)
        echo "Health check:"
        curl -s http://localhost:8088/health
        ;;
    ready)
        echo "Readiness check:"
        curl -s http://localhost:8088/ready
        ;;
    build)
        echo "Building WebP Converter image..."
        docker-compose -f $COMPOSE_FILE build $SERVICE_NAME
        echo "Build complete."
        ;;
    test)
        echo "Running WebP Converter tests..."
        docker-compose -f $COMPOSE_FILE up --build test-runner
        ;;
    exec)
        echo "Opening shell in WebP Converter container..."
        docker-compose -f $COMPOSE_FILE exec $SERVICE_NAME /bin/bash
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|stats|health|ready|build|test|exec}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the service"
        echo "  stop    - Stop the service"
        echo "  restart - Restart the service"
        echo "  logs    - Show service logs"
        echo "  stats   - Show service statistics"
        echo "  health  - Health check"
        echo "  ready   - Readiness check"
        echo "  build   - Build the Docker image"
        echo "  test    - Run tests"
        echo "  exec    - Open shell in container"
        exit 1
        ;;
esac
