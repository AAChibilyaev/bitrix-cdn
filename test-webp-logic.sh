#!/bin/bash
# WebP Logic Test Script
# Author: Chibilyaev Alexandr <info@aachibilyaev.com>

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🖼️ WebP Logic Test${NC}"
echo "===================="

# Test URL
TEST_URL="https://cdn.termokit.ru/upload/resize_cache/iblock/e0e/yclmb1ogvb3blyd5x8gt0pz1g7j3gmvj/692_500_0e9f228b13fced173205fc3f65fb74d91/Laminat-My-Step-Herringbone-MS3212-Tisa.jpg"

echo -e "\n${YELLOW}Testing WebP Logic:${NC}"

# Test 1: Original request (should return JPG)
echo -e "\n${BLUE}1. Original request (Accept: image/jpeg):${NC}"
curl -s -H "Accept: image/jpeg" -I "$TEST_URL" | grep -E "(HTTP|Content-Type|X-Cache)"

# Test 2: WebP request (should return WebP if exists)
echo -e "\n${BLUE}2. WebP request (Accept: image/webp):${NC}"
curl -s -H "Accept: image/webp" -I "$TEST_URL" | grep -E "(HTTP|Content-Type|X-Cache)"

# Test 3: AVIF request (should return AVIF if exists)
echo -e "\n${BLUE}3. AVIF request (Accept: image/avif):${NC}"
curl -s -H "Accept: image/avif" -I "$TEST_URL" | grep -E "(HTTP|Content-Type|X-Cache)"

# Test 4: Combined request (should return AVIF > WebP > JPG)
echo -e "\n${BLUE}4. Combined request (Accept: image/avif,image/webp,image/jpeg):${NC}"
curl -s -H "Accept: image/avif,image/webp,image/jpeg" -I "$TEST_URL" | grep -E "(HTTP|Content-Type|X-Cache)"

# Test 5: Check if WebP file exists
echo -e "\n${BLUE}5. Checking if WebP file exists:${NC}"
WEBP_URL="${TEST_URL%.jpg}.webp"
curl -s -I "$WEBP_URL" | grep -E "(HTTP|Content-Type)"

# Test 6: Check if AVIF file exists
echo -e "\n${BLUE}6. Checking if AVIF file exists:${NC}"
AVIF_URL="${TEST_URL%.jpg}.avif"
curl -s -I "$AVIF_URL" | grep -E "(HTTP|Content-Type)"

echo -e "\n${GREEN}✅ WebP Logic Test Complete${NC}"
