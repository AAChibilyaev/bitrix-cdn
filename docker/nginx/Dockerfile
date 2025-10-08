# Custom Nginx with Lua support for Redis/Memcached integration
# Author: Chibilyaev Alexandr <info@aachibilyaev.com>

FROM openresty/openresty:1.25.3.1-alpine

# Install additional packages
RUN apk add --no-cache \
    curl \
    redis-tools \
    memcached-tools \
    bc

# Install Lua modules
RUN /usr/local/openresty/luajit/bin/luarocks install lua-resty-redis
RUN /usr/local/openresty/luajit/bin/luarocks install lua-resty-memcached
RUN /usr/local/openresty/luajit/bin/luarocks install lua-cjson

# Create directories
RUN mkdir -p /etc/nginx/lua \
    /tmp/nginx_cache \
    /var/cache/nginx

# Copy configuration files
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/
COPY lua/ /etc/nginx/lua/
COPY html/ /usr/share/nginx/html/

# Set permissions
RUN chown -R nginx:nginx /tmp/nginx_cache /var/cache/nginx

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

EXPOSE 80 443

CMD ["/usr/local/openresty/bin/openresty", "-g", "daemon off;"]
