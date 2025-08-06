import os
import redis
from urllib.parse import urlparse

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

parsed_url = urlparse(redis_url)

redis = redis.Redis(
    host=parsed_url.hostname,
    port=parsed_url.port,
    password=parsed_url.password,
    db=0,
    decode_responses=True
)
