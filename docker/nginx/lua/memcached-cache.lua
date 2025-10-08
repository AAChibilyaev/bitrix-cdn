-- Memcached Cache Integration for Nginx
-- Author: Chibilyaev Alexandr <info@aachibilyaev.com>

local memcached = require "resty.memcached"
local cjson = require "cjson"

local _M = {}

-- Memcached connection pool
local memcached_pool = {
    host = "memcached",
    port = 11211,
    pool_size = 100,
    pool_timeout = 1000,
    pool_max_idle_time = 10000,
}

-- Get Memcached connection
local function get_memcached_conn()
    local memc = memcached:new()
    memc:set_timeout(1000) -- 1 second timeout
    
    local ok, err = memc:connect(memcached_pool.host, memcached_pool.port)
    if not ok then
        ngx.log(ngx.ERR, "Failed to connect to Memcached: ", err)
        return nil
    end
    
    return memc
end

-- Close Memcached connection
local function close_memcached_conn(memc)
    if memc then
        local ok, err = memc:set_keepalive(memcached_pool.pool_max_idle_time, memcached_pool.pool_size)
        if not ok then
            ngx.log(ngx.ERR, "Failed to set keepalive: ", err)
        end
    end
end

-- Generate cache key for Memcached
function _M.generate_cache_key()
    local uri = ngx.var.request_uri
    local accept = ngx.var.http_accept or ""
    
    -- Create unique key based on URI and headers
    local key = "cdn_mem:" .. ngx.md5(uri .. accept)
    return key
end

-- Get from Memcached cache
function _M.get_from_cache(key)
    local memc = get_memcached_conn()
    if not memc then
        return nil
    end
    
    local res, err = memc:get(key)
    close_memcached_conn(memc)
    
    if not res or res == ngx.null then
        return nil
    end
    
    -- Parse JSON response
    local ok, data = pcall(cjson.decode, res)
    if not ok then
        ngx.log(ngx.ERR, "Failed to decode JSON from Memcached: ", data)
        return nil
    end
    
    return data
end

-- Set to Memcached cache
function _M.set_to_cache(key, data, ttl)
    local memc = get_memcached_conn()
    if not memc then
        return false
    end
    
    local json_data = cjson.encode(data)
    local ok, err = memc:set(key, json_data, ttl or 3600)
    close_memcached_conn(memc)
    
    if not ok then
        ngx.log(ngx.ERR, "Failed to set cache in Memcached: ", err)
        return false
    end
    
    return true
end

-- Cache hit handler for Memcached
function _M.handle_cache_hit(cache_data)
    -- Set response headers
    ngx.header["Content-Type"] = cache_data.content_type
    ngx.header["Content-Length"] = cache_data.content_length
    ngx.header["Cache-Control"] = cache_data.cache_control
    ngx.header["X-Cache-Status"] = "HIT"
    ngx.header["X-Cache-Key"] = cache_data.cache_key
    ngx.header["X-Cache-TTL"] = cache_data.ttl
    ngx.header["X-Cache-Backend"] = "Memcached"
    
    -- Set CORS headers
    ngx.header["Access-Control-Allow-Origin"] = "*"
    ngx.header["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    ngx.header["Access-Control-Max-Age"] = "31536000"
    
    -- Send cached content
    ngx.say(cache_data.content)
    ngx.exit(200)
end

-- Cache miss handler for Memcached
function _M.handle_cache_miss()
    ngx.header["X-Cache-Status"] = "MISS"
    ngx.header["X-Cache-Backend"] = "Memcached"
    -- Continue to upstream
end

-- Cache set handler for Memcached
function _M.handle_cache_set(content, content_type, cache_control, ttl)
    local cache_data = {
        content = content,
        content_type = content_type,
        content_length = #content,
        cache_control = cache_control,
        cache_key = _M.generate_cache_key(),
        ttl = ttl,
        timestamp = os.time(),
        backend = "Memcached"
    }
    
    local key = _M.generate_cache_key()
    _M.set_to_cache(key, cache_data, ttl)
    
    ngx.header["X-Cache-Status"] = "MISS"
    ngx.header["X-Cache-Key"] = key
    ngx.header["X-Cache-Backend"] = "Memcached"
end

-- Check if request should be cached in Memcached
function _M.should_cache()
    local method = ngx.var.request_method
    local uri = ngx.var.request_uri
    
    -- Only cache GET requests
    if method ~= "GET" then
        return false
    end
    
    -- Cache images and static files
    if string.match(uri, "%.(jpg|jpeg|png|gif|bmp|webp|avif|css|js|html|xml|txt|ico|svg|woff|woff2|ttf|eot)$") then
        return true
    end
    
    return false
end

return _M
