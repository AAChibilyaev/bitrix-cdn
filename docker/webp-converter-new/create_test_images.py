#!/usr/bin/env python3
"""
Create test images for WebP converter testing
"""
import os
from PIL import Image, ImageDraw, ImageFont

def create_test_images():
    """Create test images in different formats"""
    test_dir = "test_images"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='lightblue')
    draw = ImageDraw.Draw(img)
    
    # Add some text
    try:
        # Try to use a default font
        font = ImageFont.load_default()
    except:
        font = None
    
    draw.text((50, 50), "Test Image for WebP Converter", fill='black', font=font)
    draw.text((50, 100), "This image will be converted to WebP", fill='darkblue', font=font)
    
    # Add some shapes
    draw.rectangle([100, 200, 300, 400], fill='red', outline='black', width=2)
    draw.ellipse([400, 200, 600, 400], fill='green', outline='black', width=2)
    
    # Save in different formats
    img.save(os.path.join(test_dir, 'test_image.jpg'), 'JPEG', quality=95)
    img.save(os.path.join(test_dir, 'test_image.png'), 'PNG')
    
    # Create a smaller image
    small_img = img.resize((200, 150))
    small_img.save(os.path.join(test_dir, 'small_test.jpg'), 'JPEG', quality=85)
    
    print(f"✓ Created test images in {test_dir}/")
    print("  - test_image.jpg")
    print("  - test_image.png") 
    print("  - small_test.jpg")

if __name__ == "__main__":
    create_test_images()
