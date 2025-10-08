#!/usr/bin/env python3
"""
Playwright test for WebP Converter Service
"""
import asyncio
import json
from playwright.async_api import async_playwright

async def test_webp_converter():
    """Test WebP converter endpoints"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Test health endpoint
            print("Testing health endpoint...")
            response = await page.goto("http://localhost:8088/health")
            if response and response.status == 200:
                content = await page.text_content('body')
                data = json.loads(content)
                print(f"✓ Health check: {data}")
            else:
                print(f"❌ Health check failed: {response.status if response else 'No response'}")
            
            # Test readiness endpoint
            print("Testing readiness endpoint...")
            response = await page.goto("http://localhost:8088/ready")
            if response and response.status == 200:
                content = await page.text_content('body')
                data = json.loads(content)
                print(f"✓ Readiness check: {data}")
            else:
                print(f"❌ Readiness check failed: {response.status if response else 'No response'}")
            
            # Test metrics endpoint
            print("Testing metrics endpoint...")
            response = await page.goto("http://localhost:9101/metrics")
            if response and response.status == 200:
                content = await page.text_content('body')
                print(f"✓ Metrics endpoint accessible: {len(content)} characters")
            else:
                print(f"❌ Metrics check failed: {response.status if response else 'No response'}")
            
            # Test queue status endpoint
            print("Testing queue status endpoint...")
            response = await page.goto("http://localhost:9101/queue/status")
            if response and response.status == 200:
                content = await page.text_content('body')
                data = json.loads(content)
                print(f"✓ Queue status: {data}")
            else:
                print(f"❌ Queue status failed: {response.status if response else 'No response'}")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    print("Starting WebP Converter Service tests...")
    asyncio.run(test_webp_converter())
