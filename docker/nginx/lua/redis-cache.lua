-- Redis Cache Integration for Nginx
-- Author: Chibilyaev Alexandr <info@aachibilyaev.com>

local redis = require "resty.redis"
local cjson = require "cjson"

local _M = {}

-- Redis connection pool
local redis_pool = {
    host = "redis",
    port = 6379,
    pool_size = 100,
    pool_timeout = 1000,
    pool_max_idle_time = 10000,
}

-- Get Redis connection
local function get_redis_conn()
    local red = redis:new()
    red:set_timeout(1000) -- 1 second timeout
    
    local ok, err = red:connect(redis_pool.host, redis_pool.port)
    if not ok then
        ngx.log(ngx.ERR, "Failed to connect to Redis: ", err)
        return nil
    end
    
    return red
end

-- Close Redis connection
local function close_redis_conn(red)
    if red then
        local ok, err = red:set_keepalive(redis_pool.pool_max_idle_time, redis_pool.pool_size)
        if not ok then
            ngx.log(ngx.ERR, "Failed to set keepalive: ", err)
        end
    end
end

-- Generate cache key
function _M.generate_cache_key()
    local uri = ngx.var.request_uri
    local accept = ngx.var.http_accept or ""
    local user_agent = ngx.var.http_user_agent or ""
    
    -- Create unique key based on URI and headers
    local key = "cdn:" .. ngx.md5(uri .. accept .. user_agent)
    return key
end

-- Get from Redis cache
function _M.get_from_cache(key)
    local red = get_redis_conn()
    if not red then
        return nil
    end
    
    local res, err = red:get(key)
    close_redis_conn(red)
    
    if not res or res == ngx.null then
        return nil
    end
    
    -- Parse JSON response
    local ok, data = pcall(cjson.decode, res)
    if not ok then
        ngx.log(ngx.ERR, "Failed to decode JSON from Redis: ", data)
        return nil
    end
    
    return data
end

-- Set to Redis cache
function _M.set_to_cache(key, data, ttl)
    local red = get_redis_conn()
    if not red then
        return false
    end
    
    local json_data = cjson.encode(data)
    local ok, err = red:setex(key, ttl or 3600, json_data)
    close_redis_conn(red)
    
    if not ok then
        ngx.log(ngx.ERR, "Failed to set cache in Redis: ", err)
        return false
    end
    
    return true
end

-- Cache hit handler
function _M.handle_cache_hit(cache_data)
    -- Set response headers
    ngx.header["Content-Type"] = cache_data.content_type
    ngx.header["Content-Length"] = cache_data.content_length
    ngx.header["Cache-Control"] = cache_data.cache_control
    ngx.header["X-Cache-Status"] = "HIT"
    ngx.header["X-Cache-Key"] = cache_data.cache_key
    ngx.header["X-Cache-TTL"] = cache_data.ttl
    
    -- Set CORS headers
    ngx.header["Access-Control-Allow-Origin"] = "*"
    ngx.header["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    ngx.header["Access-Control-Max-Age"] = "31536000"
    
    -- Send cached content
    ngx.say(cache_data.content)
    ngx.exit(200)
end

-- Cache miss handler
function _M.handle_cache_miss()
    ngx.header["X-Cache-Status"] = "MISS"
    -- Continue to upstream
end

-- Cache set handler
function _M.handle_cache_set(content, content_type, cache_control, ttl)
    local cache_data = {
        content = content,
        content_type = content_type,
        content_length = #content,
        cache_control = cache_control,
        cache_key = _M.generate_cache_key(),
        ttl = ttl,
        timestamp = os.time()
    }
    
    local key = _M.generate_cache_key()
    _M.set_to_cache(key, cache_data, ttl)
    
    ngx.header["X-Cache-Status"] = "MISS"
    ngx.header["X-Cache-Key"] = key
end

-- Check if request should be cached
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
