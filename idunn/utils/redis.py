import logging
from redis import ConnectionPool, RedisError
from idunn import settings

logger = logging.getLogger(__name__)
REDIS_TIMEOUT = float(settings['REDIS_TIMEOUT'])


class RedisNotConfigured(RedisError):
    pass

def get_redis_pool(db):
    redis_url = settings['REDIS_URL']
    if redis_url is None:
        # Fallback to old setting name
        redis_url = settings['WIKI_API_REDIS_URL']
        if redis_url:
            logger.warning('"WIKI_API_REDIS_URL" setting is deprecated. Use REDIS_URL instead')

    if not redis_url:
        raise RedisNotConfigured('Redis URL is not set')

    if not redis_url.startswith('redis://'):
        redis_url = 'redis://' + redis_url

    return ConnectionPool.from_url(
        url=redis_url,
        socket_timeout=REDIS_TIMEOUT,
        db=db
    )
