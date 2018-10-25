from redis import ConnectionPool, RedisError

REDIS_URL_SETTING = 'WIKI_API_REDIS_URL'
REDIS_TIMEOUT_SETTING = 'WIKI_REDIS_TIMEOUT'

class RedisNotConfigured(RedisError):
    pass

def get_redis_pool(settings, db):
    redis_url = settings[REDIS_URL_SETTING]
    redis_timeout = int(settings[REDIS_TIMEOUT_SETTING])

    if not redis_url:
        raise RedisNotConfigured('Missing redis url: %s not set' % REDIS_URL_SETTING)

    if not redis_url.startswith('redis://'):
        redis_url = 'redis://' + redis_url

    return ConnectionPool.from_url(
        url=redis_url,
        socket_timeout=redis_timeout,
        db=db
    )
