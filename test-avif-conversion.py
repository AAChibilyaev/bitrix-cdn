#!/usr/bin/env python3
"""
Test script for AVIF conversion functionality
"""
import asyncio
import tempfile
import os
from pathlib import Path
from PIL import Image
import time

async def test_avif_conversion():
    """Test AVIF conversion functionality"""
    print("🧪 Testing AVIF conversion...")
    
    # Create test images
    test_images = []
    
    # Create different test images
    sizes = [(100, 100), (500, 500), (1000, 1000)]
    colors = ['red', 'blue', 'green', 'yellow', 'purple']
    
    for i, (size, color) in enumerate(zip(sizes, colors)):
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            img = Image.new('RGB', size, color=color)
            img.save(tmp.name, 'JPEG', quality=95)
            test_images.append(tmp.name)
            print(f"✅ Created test image {i+1}: {size[0]}x{size[1]} {color}")
    
    # Test AVIF conversion
    print("\n🔄 Testing AVIF conversion...")
    avif_files = []
    
    for i, jpg_path in enumerate(test_images):
        avif_path = jpg_path.replace('.jpg', '.avif')
        
        try:
            start_time = time.time()
            
            # Convert to AVIF
            with Image.open(jpg_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGBA')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save as AVIF
                img.save(avif_path, 'AVIF', quality=80, method=6)
            
            conversion_time = time.time() - start_time
            original_size = os.path.getsize(jpg_path)
            avif_size = os.path.getsize(avif_path)
            compression_ratio = (1 - avif_size / original_size) * 100
            
            print(f"✅ Image {i+1}: {original_size} → {avif_size} bytes "
                  f"({compression_ratio:.1f}% compression, {conversion_time:.2f}s)")
            
            avif_files.append(avif_path)
            
        except Exception as e:
            print(f"❌ Failed to convert image {i+1}: {e}")
    
    # Test WebP conversion for comparison
    print("\n🔄 Testing WebP conversion for comparison...")
    webp_files = []
    
    for i, jpg_path in enumerate(test_images):
        webp_path = jpg_path.replace('.jpg', '.webp')
        
        try:
            start_time = time.time()
            
            # Convert to WebP
            with Image.open(jpg_path) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGBA')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img.save(webp_path, 'WEBP', quality=85, method=6)
            
            conversion_time = time.time() - start_time
            original_size = os.path.getsize(jpg_path)
            webp_size = os.path.getsize(webp_path)
            compression_ratio = (1 - webp_size / original_size) * 100
            
            print(f"✅ Image {i+1}: {original_size} → {webp_size} bytes "
                  f"({compression_ratio:.1f}% compression, {conversion_time:.2f}s)")
            
            webp_files.append(webp_path)
            
        except Exception as e:
            print(f"❌ Failed to convert image {i+1}: {e}")
    
    # Compare formats
    print("\n📊 Format comparison:")
    for i, (jpg_path, webp_path, avif_path) in enumerate(zip(test_images, webp_files, avif_files)):
        jpg_size = os.path.getsize(jpg_path)
        webp_size = os.path.getsize(webp_path)
        avif_size = os.path.getsize(avif_path)
        
        webp_compression = (1 - webp_size / jpg_size) * 100
        avif_compression = (1 - avif_size / jpg_size) * 100
        avif_vs_webp = (1 - avif_size / webp_size) * 100
        
        print(f"Image {i+1}:")
        print(f"  JPEG: {jpg_size:,} bytes")
        print(f"  WebP: {webp_size:,} bytes ({webp_compression:.1f}% compression)")
        print(f"  AVIF: {avif_size:,} bytes ({avif_compression:.1f}% compression)")
        print(f"  AVIF vs WebP: {avif_vs_webp:.1f}% smaller")
        print()
    
    # Cleanup
    print("🧹 Cleaning up test files...")
    for file_path in test_images + webp_files + avif_files:
        try:
            os.unlink(file_path)
        except:
            pass
    
    print("✅ AVIF conversion test completed!")

if __name__ == "__main__":
    asyncio.run(test_avif_conversion())
