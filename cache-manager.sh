#!/bin/bash
# Cache Manager for Bitrix CDN Server
# Author: Chibilyaev Alexandr <info@aachibilyaev.com>

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🗄️ Bitrix CDN Cache Manager${NC}"
echo "================================"

# Redis cache management
redis_stats() {
    echo -e "\n${BLUE}📊 Redis Cache Statistics${NC}"
    echo "============================="
    
    # Redis info
    local redis_info=$(docker exec cdn-redis redis-cli info memory | grep used_memory_human)
    echo "Redis memory usage: $redis_info"
    
    # Redis keys count
    local keys=$(docker exec cdn-redis redis-cli dbsize)
    echo "Redis keys count: $keys"
    
    # Redis hit rate
    local hits=$(docker exec cdn-redis redis-cli info stats | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
    local misses=$(docker exec cdn-redis redis-cli info stats | grep keyspace_misses | cut -d: -f2 | tr -d '\r')
    if [ "$hits" -gt 0 ] || [ "$misses" -gt 0 ]; then
        local hit_rate=$(echo "scale=2; $hits * 100 / ($hits + $misses)" | bc -l 2>/dev/null || echo "0")
        echo "Redis hit rate: ${hit_rate}%"
    fi
    
    # Redis connected clients
    local clients=$(docker exec cdn-redis redis-cli info clients | grep connected_clients | cut -d: -f2 | tr -d '\r')
    echo "Connected clients: $clients"
    
    # Redis operations per second
    local ops=$(docker exec cdn-redis redis-cli info stats | grep instantaneous_ops_per_sec | cut -d: -f2 | tr -d '\r')
    echo "Operations per second: $ops"
}

# Memcached removed - Redis is sufficient for caching

# Nginx cache management
nginx_cache_stats() {
    echo -e "\n${BLUE}📊 Nginx Cache Statistics${NC}"
    echo "=============================="
    
    # Nginx cache directory size
    local cache_size=$(docker exec cdn-nginx du -sh /tmp/nginx_cache 2>/dev/null | awk '{print $1}' || echo "0")
    echo "Nginx cache size: $cache_size"
    
    # Nginx cache files count
    local cache_files=$(docker exec cdn-nginx find /tmp/nginx_cache -type f 2>/dev/null | wc -l || echo "0")
    echo "Nginx cache files: $cache_files"
    
    # Nginx memory usage
    local nginx_mem=$(docker stats cdn-nginx --no-stream --format "table {{.MemUsage}}" | tail -1)
    echo "Nginx memory usage: $nginx_mem"
}

# Clear Redis cache
clear_redis() {
    echo -e "\n${YELLOW}🗑️ Clearing Redis cache...${NC}"
    docker exec cdn-redis redis-cli flushall
    echo -e "${GREEN}✅ Redis cache cleared${NC}"
}

# Memcached removed - Redis is sufficient for caching

# Clear Nginx cache
clear_nginx() {
    echo -e "\n${YELLOW}🗑️ Clearing Nginx cache...${NC}"
    docker exec cdn-nginx rm -rf /tmp/nginx_cache/*
    echo -e "${GREEN}✅ Nginx cache cleared${NC}"
}

# Clear all caches
clear_all() {
    echo -e "\n${YELLOW}🗑️ Clearing all caches...${NC}"
    clear_redis
    # Memcached removed
    clear_nginx
    echo -e "${GREEN}✅ All caches cleared${NC}"
}

# Cache warming
warm_cache() {
    echo -e "\n${BLUE}🔥 Warming up caches...${NC}"
    
    # Warm up with common requests
    local urls=(
        "/health"
        "/nginx_status"
        "/upload/resize_cache/test.jpg"
        "/upload/resize_cache/test.webp"
        "/upload/resize_cache/test.avif"
    )
    
    for url in "${urls[@]}"; do
        echo "Warming: $url"
        curl -s "http://localhost$url" > /dev/null 2>&1 || true
    done
    
    echo -e "${GREEN}✅ Cache warming complete${NC}"
}

# Cache optimization
optimize_cache() {
    echo -e "\n${BLUE}⚡ Optimizing caches...${NC}"
    
    # Redis optimization
    echo "Optimizing Redis..."
    docker exec cdn-redis redis-cli config set maxmemory-policy allkeys-lru
    docker exec cdn-redis redis-cli config set save ""
    
    # Memcached removed - Redis is sufficient for caching
    
    # Nginx optimization
    echo "Optimizing Nginx..."
    docker exec cdn-nginx nginx -s reload
    
    echo -e "${GREEN}✅ Cache optimization complete${NC}"
}

# Main function
main() {
    case "$1" in
        redis-stats)
            redis_stats
            ;;
        nginx-cache)
            nginx_cache_stats
            ;;
        clear-redis)
            clear_redis
            ;;
        clear-nginx)
            clear_nginx
            ;;
        clear-all)
            clear_all
            ;;
        warm)
            warm_cache
            ;;
        optimize)
            optimize_cache
            ;;
        *)
            echo "Usage: $0 {redis-stats|nginx-cache|clear-redis|clear-nginx|clear-all|warm|optimize}"
            echo ""
            echo "Commands:"
            echo "  redis-stats     - Show Redis cache statistics"
            echo "  nginx-cache     - Show Nginx cache statistics"
            echo "  clear-redis      - Clear Redis cache"
            echo "  clear-nginx     - Clear Nginx cache"
            echo "  clear-all       - Clear all caches"
            echo "  warm            - Warm up caches"
            echo "  optimize        - Optimize cache settings"
            exit 1
            ;;
    esac
}

# Run
main "$@"
