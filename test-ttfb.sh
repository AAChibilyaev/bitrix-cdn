#!/bin/bash
# TTFB Performance Test Script
# Author: Chibilyaev Alexandr <info@aachibilyaev.com>

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 TTFB Performance Test${NC}"
echo "=========================="

# Test URLs
URLS=(
    "http://localhost/health"
    "http://localhost/nginx_status"
    "http://localhost/upload/resize_cache/test.jpg"
    "http://localhost/upload/resize_cache/test.webp"
    "http://localhost/upload/resize_cache/test.avif"
)

# Test function
test_ttfb() {
    local url=$1
    echo -e "\n${YELLOW}Testing: $url${NC}"
    
    # Test with curl
    local start_time=$(date +%s%N)
    local response=$(curl -s -w "%{http_code}|%{time_total}|%{time_namelookup}|%{time_connect}|%{time_appconnect}|%{time_pretransfer}|%{time_starttransfer}" -o /dev/null "$url" 2>/dev/null || echo "000|0.000|0.000|0.000|0.000|0.000|0.000")
    local end_time=$(date +%s%N)
    
    # Parse response
    IFS='|' read -r http_code time_total time_namelookup time_connect time_appconnect time_pretransfer time_starttransfer <<< "$response"
    
    # Calculate TTFB (Time To First Byte)
    local ttfb=$(echo "$time_starttransfer" | bc -l 2>/dev/null || echo "0")
    local ttfb_ms=$(echo "$ttfb * 1000" | bc -l 2>/dev/null || echo "0")
    
    # Color coding for TTFB
    if (( $(echo "$ttfb_ms < 50" | bc -l) )); then
        local color=$GREEN
        local status="EXCELLENT"
    elif (( $(echo "$ttfb_ms < 100" | bc -l) )); then
        local color=$YELLOW
        local status="GOOD"
    else
        local color=$RED
        local status="SLOW"
    fi
    
    echo "  HTTP Code: $http_code"
    echo "  TTFB: ${color}${ttfb_ms}ms${NC} ($status)"
    echo "  Total Time: ${time_total}s"
    echo "  DNS Lookup: ${time_namelookup}s"
    echo "  Connect: ${time_connect}s"
    echo "  App Connect: ${time_appconnect}s"
    echo "  Pre Transfer: ${time_pretransfer}s"
    echo "  Start Transfer: ${time_starttransfer}s"
}

# Test all URLs
for url in "${URLS[@]}"; do
    test_ttfb "$url"
done

echo -e "\n${BLUE}📊 Performance Summary${NC}"
echo "======================"

# Test with different Accept headers
echo -e "\n${YELLOW}Testing with different Accept headers:${NC}"

# Test WebP support
echo -e "\n${BLUE}WebP Support Test:${NC}"
curl -s -H "Accept: image/webp" -w "TTFB: %{time_starttransfer}s\n" -o /dev/null "http://localhost/upload/resize_cache/test.jpg" 2>/dev/null || echo "Failed"

# Test AVIF support
echo -e "\n${BLUE}AVIF Support Test:${NC}"
curl -s -H "Accept: image/avif" -w "TTFB: %{time_starttransfer}s\n" -o /dev/null "http://localhost/upload/resize_cache/test.jpg" 2>/dev/null || echo "Failed"

# Test original format
echo -e "\n${BLUE}Original Format Test:${NC}"
curl -s -H "Accept: image/jpeg" -w "TTFB: %{time_starttransfer}s\n" -o /dev/null "http://localhost/upload/resize_cache/test.jpg" 2>/dev/null || echo "Failed"

echo -e "\n${GREEN}✅ TTFB Test Complete${NC}"
