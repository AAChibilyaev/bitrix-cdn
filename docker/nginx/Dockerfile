# Custom Nginx with Lua support for Redis/Memcached integration
# Author: Chibilyaev Alexandr <info@aachibilyaev.com>

FROM nginx:1.25-alpine

# Install additional packages
RUN apk add --no-cache \
    curl \
    redis \
    bc

# Lua modules removed - not needed for current configuration

# Create directories
RUN mkdir -p /etc/nginx/lua \
    /tmp/nginx_cache \
    /var/cache/nginx \
    /var/www/cdn/upload/resize_cache

# Copy configuration files
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/
COPY lua/ /etc/nginx/lua/
COPY html/ /usr/share/nginx/html/

# Remove default.conf to avoid conflicts
RUN rm -f /etc/nginx/conf.d/default.conf

# Set permissions
RUN chown -R nobody:nobody /tmp/nginx_cache /var/cache/nginx /var/www/cdn

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
