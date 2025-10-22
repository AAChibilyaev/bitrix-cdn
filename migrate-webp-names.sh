#!/bin/bash
# Migrate WebP/AVIF file names from old format to new format
# Old: image.jpg.webp -> New: image.webp
# Old: image.jpg.avif -> New: image.avif

echo "🔄 Starting WebP/AVIF file name migration..."

# Count files before migration
echo "📊 Counting files before migration..."
jpg_webp_count=$(find /var/www/cdn/upload/resize_cache -name "*.jpg.webp" | wc -l)
jpeg_webp_count=$(find /var/www/cdn/upload/resize_cache -name "*.jpeg.webp" | wc -l)
png_webp_count=$(find /var/www/cdn/upload/resize_cache -name "*.png.webp" | wc -l)
jpg_avif_count=$(find /var/www/cdn/upload/resize_cache -name "*.jpg.avif" | wc -l)
jpeg_avif_count=$(find /var/www/cdn/upload/resize_cache -name "*.jpeg.avif" | wc -l)
png_avif_count=$(find /var/www/cdn/upload/resize_cache -name "*.png.avif" | wc -l)

total_files=$((jpg_webp_count + jpeg_webp_count + png_webp_count + jpg_avif_count + jpeg_avif_count + png_avif_count))

echo "📈 Files to migrate:"
echo "  - *.jpg.webp: $jpg_webp_count"
echo "  - *.jpeg.webp: $jpeg_webp_count"
echo "  - *.png.webp: $png_webp_count"
echo "  - *.jpg.avif: $jpg_avif_count"
echo "  - *.jpeg.avif: $jpeg_avif_count"
echo "  - *.png.avif: $png_avif_count"
echo "  - Total: $total_files"

if [ $total_files -eq 0 ]; then
    echo "✅ No files to migrate. Migration complete."
    exit 0
fi

echo ""
echo "🔄 Starting migration..."

# Migrate WebP files
echo "📝 Migrating WebP files..."
find /var/www/cdn/upload/resize_cache -name "*.jpg.webp" -exec bash -c 'mv "$0" "${0%.jpg.webp}.webp"' {} \;
find /var/www/cdn/upload/resize_cache -name "*.jpeg.webp" -exec bash -c 'mv "$0" "${0%.jpeg.webp}.webp"' {} \;
find /var/www/cdn/upload/resize_cache -name "*.png.webp" -exec bash -c 'mv "$0" "${0%.png.webp}.webp"' {} \;

# Migrate AVIF files
echo "📝 Migrating AVIF files..."
find /var/www/cdn/upload/resize_cache -name "*.jpg.avif" -exec bash -c 'mv "$0" "${0%.jpg.avif}.avif"' {} \;
find /var/www/cdn/upload/resize_cache -name "*.jpeg.avif" -exec bash -c 'mv "$0" "${0%.jpeg.avif}.avif"' {} \;
find /var/www/cdn/upload/resize_cache -name "*.png.avif" -exec bash -c 'mv "$0" "${0%.png.avif}.avif"' {} \;

# Count files after migration
echo ""
echo "📊 Verifying migration..."
jpg_webp_after=$(find /var/www/cdn/upload/resize_cache -name "*.jpg.webp" | wc -l)
jpeg_webp_after=$(find /var/www/cdn/upload/resize_cache -name "*.jpeg.webp" | wc -l)
png_webp_after=$(find /var/www/cdn/upload/resize_cache -name "*.png.webp" | wc -l)
jpg_avif_after=$(find /var/www/cdn/upload/resize_cache -name "*.jpg.avif" | wc -l)
jpeg_avif_after=$(find /var/www/cdn/upload/resize_cache -name "*.jpeg.avif" | wc -l)
png_avif_after=$(find /var/www/cdn/upload/resize_cache -name "*.png.avif" | wc -l)

old_format_remaining=$((jpg_webp_after + jpeg_webp_after + png_webp_after + jpg_avif_after + jpeg_avif_after + png_avif_after))

echo "📈 Files remaining in old format: $old_format_remaining"

if [ $old_format_remaining -eq 0 ]; then
    echo "✅ Migration completed successfully!"
    echo "🎯 All WebP/AVIF files have been renamed to the new format."
else
    echo "⚠️  Warning: $old_format_remaining files still in old format"
    echo "🔍 Please check manually for any issues"
fi

echo ""
echo "🎉 Migration script completed!"
