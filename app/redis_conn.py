import os
import redis
from urllib.parse import urlparse

redis_url = os.getenv("REDIS_URL")

parsed_url = urlparse(redis_url)

redis = redis.Redis(
    host=parsed_url.hostname,
    port=parsed_url.port,
    password=parsed_url.password,
    decode_responses=True  # ✅ Do NOT use ssl=True
)
