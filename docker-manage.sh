#!/bin/bash
# Docker CDN Management Script
# Author: Chibilyaev Alexandr <info@aachibilyaev.com>
# Company: AAChibilyaev LTD

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Functions
print_help() {
    echo "Docker CDN Server Management"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  setup       - Initial setup (create directories, copy configs)"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  status      - Show service status"
    echo "  logs        - Show logs (use -f for follow)"
    echo "  build       - Build custom images"
    echo "  shell       - Open shell in container"
    echo "  clean       - Clean WebP/AVIF cache"
    echo "  stats       - Show cache statistics"
    echo "  perf        - Performance monitoring"
    echo "  cache       - Cache management"
    echo "  avif        - AVIF converter management"
    echo "  telegram-bot - Telegram Bot management"
    echo "  backup      - Backup configuration"
    echo "  restore     - Restore from backup"
    echo "  ssl         - Setup SSL certificates"
    echo ""
    echo "Options:"
    echo "  -d          - Use development compose file"
    echo "  -f          - Follow logs"
    echo "  -h          - Show this help"
}

# Check prerequisites
check_requirements() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}Docker Compose is not installed${NC}"
        exit 1
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}Creating .env file from template...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}Please edit .env file with your configuration${NC}"
        exit 1
    fi
}

# Setup directories and files
setup() {
    echo -e "${BLUE}Setting up CDN server...${NC}"
    
    # Create directories
    mkdir -p docker/ssh
    mkdir -p docker/ssl
    mkdir -p docker/certbot/www
    mkdir -p docker/certbot/conf
    mkdir -p logs/{nginx,converter,sshfs}
    
    # Copy SSH key
    if [ ! -f "docker/ssh/bitrix_mount" ]; then
        echo -e "${YELLOW}Generating SSH key...${NC}"
        ssh-keygen -t rsa -b 4096 -f docker/ssh/bitrix_mount -N ""
        echo ""
        echo -e "${GREEN}SSH public key:${NC}"
        cat docker/ssh/bitrix_mount.pub
        echo ""
        echo -e "${YELLOW}Add this key to your Bitrix server's authorized_keys${NC}"
    fi
    
    # Set permissions
    chmod 600 docker/ssh/bitrix_mount
    chmod 644 docker/ssh/bitrix_mount.pub
    
    echo -e "${GREEN}Setup complete!${NC}"
}

# Start services
start_services() {
    echo -e "${BLUE}Starting CDN services...${NC}"
    docker compose -f "$COMPOSE_FILE" up -d
    
    sleep 5
    show_status
}

# Stop services
stop_services() {
    echo -e "${BLUE}Stopping CDN services...${NC}"
    docker compose -f "$COMPOSE_FILE" down
}

# Restart services
restart_services() {
    echo -e "${BLUE}Restarting CDN services...${NC}"
    docker compose -f "$COMPOSE_FILE" restart
    
    sleep 5
    show_status
}

# Show status
show_status() {
    echo -e "${BLUE}Service Status:${NC}"
    docker compose -f "$COMPOSE_FILE" ps
    
    echo ""
    echo -e "${BLUE}Health Checks:${NC}"
    
    # ИСПРАВЛЕНО: Check NGINX (правильный порт)
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:80/health" | grep -q "200"; then
        echo -e "${GREEN}✓ NGINX is healthy${NC}"
    else
        echo -e "${RED}✗ NGINX is not responding${NC}"
    fi
    
    # Check Redis
    local redis_password="${REDIS_PASSWORD:-bitrix_cdn_secure_2024}"
    if docker exec cdn-redis redis-cli -a "$redis_password" ping | grep -q "PONG"; then
        echo -e "${GREEN}✓ Redis is healthy${NC}"
    else
        echo -e "${RED}✗ Redis is not responding${NC}"
    fi
    
    # ИСПРАВЛЕНО: Check mount с правильным container name
    if docker exec cdn-sshfs ls /mnt/bitrix > /dev/null 2>&1; then
        echo -e "${GREEN}✓ SSHFS mount is working${NC}"
    else
        echo -e "${RED}✗ SSHFS mount failed${NC}"
    fi
}

# Show logs
show_logs() {
    if [ "$1" = "-f" ]; then
        docker compose -f "$COMPOSE_FILE" logs -f
    else
        docker compose -f "$COMPOSE_FILE" logs --tail=50
    fi
}

# Build images
build_images() {
    echo -e "${BLUE}Building custom images...${NC}"
    docker compose -f "$COMPOSE_FILE" build
}

# Open shell in container
open_shell() {
    local container="${1:-nginx}"
    echo -e "${BLUE}Opening shell in $container container...${NC}"
    docker exec -it "cdn-$container" /bin/sh
}

# Clean cache
# ИСПРАВЛЕНО: Clean cache с правильным container name
clean_cache() {
    echo -e "${BLUE}Cleaning WebP/AVIF cache...${NC}"
    docker exec cdn-webp-converter find /var/cache/webp -type f -name "*.webp" -mtime +7 -delete
    docker exec cdn-webp-converter find /var/cache/webp -type f -name "*.avif" -mtime +7 -delete
    echo -e "${GREEN}Cache cleaned${NC}"
}

# Show statistics
show_stats() {
    echo -e "${BLUE}Cache Statistics:${NC}"
    
    # WebP files count
    local webp_count=$(docker exec cdn-webp-converter find /var/cache/webp -type f -name "*.webp" 2>/dev/null | wc -l)
    echo "WebP files: $webp_count"
    
    # AVIF files count
    local avif_count=$(docker exec cdn-webp-converter find /var/cache/webp -type f -name "*.avif" 2>/dev/null | wc -l)
    echo "AVIF files: $avif_count"
    
    # Cache size
    local cache_size=$(docker exec cdn-webp-converter du -sh /var/cache/webp 2>/dev/null | cut -f1)
    echo "Cache size: $cache_size"
    
    # Redis stats
    echo ""
    echo "Redis stats:"
    docker exec cdn-redis redis-cli info stats | grep -E "total_connections_received|instantaneous_ops_per_sec|used_memory_human"
}

# Backup
backup() {
    local backup_name="cdn-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    echo -e "${BLUE}Creating backup: $backup_name${NC}"
    
    tar -czf "$backup_name" \
        .env \
        docker/ \
        --exclude=docker/ssh/bitrix_mount \
        --exclude=docker/certbot/conf
    
    echo -e "${GREEN}Backup created: $backup_name${NC}"
}

# Setup SSL
setup_ssl() {
    echo -e "${BLUE}Setting up SSL certificates...${NC}"
    
    # Get domain from .env
    source .env
    
    if [ -z "$CDN_DOMAIN" ]; then
        echo -e "${RED}CDN_DOMAIN not set in .env${NC}"
        exit 1
    fi
    
    # Request certificate
    docker run -it --rm \
        -v $(pwd)/docker/certbot/conf:/etc/letsencrypt \
        -v $(pwd)/docker/certbot/www:/var/www/certbot \
        certbot/certbot \
        certonly --webroot \
        -w /var/www/certbot \
        -d "$CDN_DOMAIN" \
        --email "$LETSENCRYPT_EMAIL" \
        --agree-tos \
        --no-eff-email
    
    echo -e "${GREEN}SSL certificate obtained${NC}"
    echo -e "${YELLOW}Uncomment SSL configuration in docker/nginx/conf.d/default.conf${NC}"
}

# AVIF management
avif_management() {
    echo -e "${BLUE}AVIF Converter Management${NC}"
    echo ""
    echo "Available commands:"
    echo "  start       - Start AVIF converter"
    echo "  stop        - Stop AVIF converter"
    echo "  restart     - Restart AVIF converter"
    echo "  logs        - Show converter logs"
    echo "  stats       - Show conversion statistics"
    echo "  test        - Test AVIF conversion"
    echo "  enable-avif - Enable AVIF conversion"
    echo "  disable-avif- Disable AVIF conversion"
    echo ""
    echo "Usage: ./avif-ctl.sh [command]"
}

# Main
main() {
    # Parse options
    while getopts "dfh" opt; do
        case $opt in
            d)
                COMPOSE_FILE="docker-compose.dev.yml"
                ;;
            f)
                FOLLOW_LOGS=true
                ;;
            h)
                print_help
                exit 0
                ;;
            \?)
                echo "Invalid option: -$OPTARG"
                print_help
                exit 1
                ;;
        esac
    done
    
    shift $((OPTIND-1))
    
    # Check requirements
    check_requirements
    
    # Execute command
    case "${1:-help}" in
        setup)
            setup
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            if [ "$FOLLOW_LOGS" = true ]; then
                show_logs -f
            else
                show_logs
            fi
            ;;
        build)
            build_images
            ;;
        shell)
            open_shell "$2"
            ;;
        clean)
            clean_cache
            ;;
        stats)
            show_stats
            ;;
        backup)
            backup
            ;;
        ssl)
            setup_ssl
            ;;
        avif)
        avif_management
        ;;
    perf)
        echo -e "${BLUE}Running performance monitoring...${NC}"
        ./performance-monitor.sh
        ;;
    cache)
        echo -e "${BLUE}Cache Management${NC}"
        echo ""
        if [ -n "$2" ]; then
            ./cache-manager.sh "$2"
        else
            echo "Available commands:"
            echo "  redis-stats     - Redis cache statistics"
            # Memcached removed
            echo "  nginx-cache     - Nginx cache statistics"
            echo "  clear-redis     - Clear Redis cache"
            # Memcached removed
            echo "  clear-nginx     - Clear Nginx cache"
            echo "  clear-all       - Clear all caches"
            echo "  warm            - Warm up caches"
            echo "  optimize        - Optimize cache settings"
            echo ""
            echo "Usage: ./docker-manage.sh cache [command]"
        fi
        ;;
    telegram-bot)
        if [ -n "$2" ]; then
            case "$2" in
                start)
                    echo -e "${BLUE}🤖 Starting Telegram Bot...${NC}"
                    docker compose up -d telegram-bot
                    echo -e "${GREEN}✅ Telegram Bot started${NC}"
                    ;;
                stop)
                    echo -e "${BLUE}🤖 Stopping Telegram Bot...${NC}"
                    docker compose stop telegram-bot
                    echo -e "${GREEN}✅ Telegram Bot stopped${NC}"
                    ;;
                restart)
                    echo -e "${BLUE}🤖 Restarting Telegram Bot...${NC}"
                    docker compose restart telegram-bot
                    echo -e "${GREEN}✅ Telegram Bot restarted${NC}"
                    ;;
                logs)
                    echo -e "${BLUE}🤖 Telegram Bot logs:${NC}"
                    docker logs -f cdn-telegram-bot
                    ;;
                status)
                    echo -e "${BLUE}🤖 Telegram Bot status:${NC}"
                    docker ps --filter name=cdn-telegram-bot --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
                    ;;
                build)
                    echo -e "${BLUE}🤖 Building Telegram Bot...${NC}"
                    docker compose build telegram-bot
                    echo -e "${GREEN}✅ Telegram Bot built${NC}"
                    ;;
                *)
                    echo -e "${YELLOW}Available telegram-bot commands:${NC}"
                    echo "  start     - Start Telegram Bot"
                    echo "  stop      - Stop Telegram Bot"
                    echo "  restart   - Restart Telegram Bot"
                    echo "  logs      - Show Telegram Bot logs"
                    echo "  status    - Show Telegram Bot status"
                    echo "  build     - Build Telegram Bot image"
                    echo ""
                    echo "Usage: ./docker-manage.sh telegram-bot [command]"
                    ;;
            esac
        else
            echo -e "${YELLOW}Available telegram-bot commands:${NC}"
            echo "  start     - Start Telegram Bot"
            echo "  stop      - Stop Telegram Bot"
            echo "  restart   - Restart Telegram Bot"
            echo "  logs      - Show Telegram Bot logs"
            echo "  status    - Show Telegram Bot status"
            echo "  build     - Build Telegram Bot image"
            echo ""
            echo "Usage: ./docker-manage.sh telegram-bot [command]"
        fi
        ;;
    help|*)
        print_help
        ;;
esac
}

# Run
main "$@"
