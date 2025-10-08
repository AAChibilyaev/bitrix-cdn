#!/bin/bash
# Performance Monitor for Bitrix CDN Server
# Author: Chibilyaev Alexandr <info@aachibilyaev.com>

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 Bitrix CDN Performance Monitor${NC}"
echo "=================================="

# Check if services are running
check_service() {
    local service=$1
    local port=$2
    local name=$3
    
    case $service in
        "nginx")
            if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
                echo -e "${GREEN}✅ $name${NC} - Running on port $port"
                return 0
            else
                echo -e "${RED}❌ $name${NC} - Not responding on port $port"
                return 1
            fi
            ;;
        "redis")
            if docker exec cdn-redis redis-cli ping > /dev/null 2>&1; then
                echo -e "${GREEN}✅ $name${NC} - Running on port $port"
                return 0
            else
                echo -e "${RED}❌ $name${NC} - Not responding on port $port"
                return 1
            fi
            ;;
        # Memcached removed
        "prometheus")
            if curl -s -f "http://localhost:$port/-/healthy" > /dev/null 2>&1; then
                echo -e "${GREEN}✅ $name${NC} - Running on port $port"
                return 0
            else
                echo -e "${RED}❌ $name${NC} - Not responding on port $port"
                return 1
            fi
            ;;
        "grafana")
            if curl -s -f "http://localhost:$port/api/health" > /dev/null 2>&1; then
                echo -e "${GREEN}✅ $name${NC} - Running on port $port"
                return 0
            else
                echo -e "${RED}❌ $name${NC} - Not responding on port $port"
                return 1
            fi
            ;;
        "webp-converter")
            if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
                echo -e "${GREEN}✅ $name${NC} - Running on port $port"
                return 0
            else
                echo -e "${RED}❌ $name${NC} - Not responding on port $port"
                return 1
            fi
            ;;
        *)
            if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
                echo -e "${GREEN}✅ $name${NC} - Running on port $port"
                return 0
            else
                echo -e "${RED}❌ $name${NC} - Not responding on port $port"
                return 1
            fi
            ;;
    esac
}

# Performance metrics
get_nginx_stats() {
    echo -e "\n${BLUE}📊 NGINX Performance Metrics${NC}"
    echo "================================"
    
    # Active connections
    local active=$(curl -s http://localhost/nginx_status | grep "Active connections" | awk '{print $3}')
    echo "Active connections: $active"
    
    # Requests per second
    local requests=$(curl -s http://localhost/nginx_status | grep "server requests handled" | awk '{print $1}')
    echo "Total requests: $requests"
    
    # Memory usage
    local nginx_mem=$(docker stats cdn-nginx --no-stream --format "table {{.MemUsage}}" | tail -1)
    echo "Nginx memory usage: $nginx_mem"
}

get_redis_stats() {
    echo -e "\n${BLUE}📊 Redis Performance Metrics${NC}"
    echo "================================"
    
    # Redis info
    local redis_info=$(docker exec cdn-redis redis-cli info memory | grep used_memory_human)
    echo "Redis memory usage: $redis_info"
    
    # Redis keys
    local keys=$(docker exec cdn-redis redis-cli dbsize)
    echo "Redis keys count: $keys"
    
    # Redis hit rate
    local hits=$(docker exec cdn-redis redis-cli info stats | grep keyspace_hits | cut -d: -f2 | tr -d '\r')
    local misses=$(docker exec cdn-redis redis-cli info stats | grep keyspace_misses | cut -d: -f2 | tr -d '\r')
    if [ "$hits" -gt 0 ] || [ "$misses" -gt 0 ]; then
        local hit_rate=$(echo "scale=2; $hits * 100 / ($hits + $misses)" | bc -l 2>/dev/null || echo "0")
        echo "Redis hit rate: ${hit_rate}%"
    fi
}

# Memcached removed - Redis is sufficient for caching

get_system_stats() {
    echo -e "\n${BLUE}📊 System Performance Metrics${NC}"
    echo "=================================="
    
    # CPU usage
    local cpu_usage=$(docker stats --no-stream --format "table {{.CPUPerc}}" | grep -v "CPU" | head -1)
    echo "CPU usage: $cpu_usage"
    
    # Memory usage
    local mem_usage=$(docker stats --no-stream --format "table {{.MemUsage}}" | grep -v "MEM" | head -1)
    echo "Memory usage: $mem_usage"
    
    # Disk usage
    local disk_usage=$(df -h / | tail -1 | awk '{print $5}')
    echo "Disk usage: $disk_usage"
}

# Cache performance test
test_cache_performance() {
    echo -e "\n${BLUE}🧪 Cache Performance Test${NC}"
    echo "============================="
    
    # Test image request
    local start_time=$(date +%s%N)
    curl -s -o /dev/null "http://localhost/health"
    local end_time=$(date +%s%N)
    local response_time=$(( (end_time - start_time) / 1000000 ))
    
    echo "Health check response time: ${response_time}ms"
    
    # Test with cache headers
    local cache_headers=$(curl -s -I "http://localhost/health" | grep -i "cache\|x-cache")
    echo "Cache headers: $cache_headers"
}

# Main monitoring function
main() {
    echo -e "\n${BLUE}🔍 Service Status Check${NC}"
    echo "=========================="
    
    # Check all services
    check_service "nginx" "80" "Nginx Web Server"
    check_service "redis" "6379" "Redis Cache"
    # Memcached removed
    check_service "webp-converter" "8088" "WebP Converter"
    check_service "prometheus" "9090" "Prometheus"
    check_service "grafana" "3000" "Grafana"
    
    # Get performance metrics
    get_nginx_stats
    get_redis_stats
    # Memcached removed
    get_system_stats
    
    # Test cache performance
    test_cache_performance
    
    echo -e "\n${GREEN}✅ Performance monitoring complete${NC}"
}

# Run monitoring
main
