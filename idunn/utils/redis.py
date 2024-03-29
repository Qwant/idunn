import json
import logging
from redis import Redis, ConnectionPool, RedisError
from idunn import settings
from idunn.utils import prometheus

logger = logging.getLogger(__name__)
REDIS_TIMEOUT = float(settings["REDIS_TIMEOUT"])

DISABLED_STATE = object()  # Used to flag cache as disabled by settings


class RedisNotConfigured(RedisError):
    pass


def get_redis_pool(db):
    redis_url = settings["REDIS_URL"]
    if redis_url is None:
        # Fallback to old setting name
        redis_url = settings["WIKI_API_REDIS_URL"]
        if redis_url:
            logger.warning('"WIKI_API_REDIS_URL" setting is deprecated. Use REDIS_URL instead')

    if not redis_url:
        raise RedisNotConfigured("Redis URL is not set")

    if not redis_url.startswith("redis://"):
        redis_url = "redis://" + redis_url
    return ConnectionPool.from_url(url=redis_url, socket_timeout=REDIS_TIMEOUT, db=db)


class CacheNotAvailable(Exception):
    pass


class RedisWrapper:
    _connection = None

    @classmethod
    def _set_value(cls, key, value, expire=settings["WIKI_CACHE_TIMEOUT"], raise_on_error=False):
        try:
            cls._connection.set(key, value, ex=expire)
        except RedisError:
            prometheus.exception("RedisError")
            if raise_on_error:
                raise
            logging.exception("Got a RedisError")

    @classmethod
    def _get_value(cls, key):
        try:
            value_stored = cls._connection.get(key)
            return value_stored
        except RedisError as exc:
            prometheus.exception("RedisError")
            raise CacheNotAvailable from exc

    @classmethod
    def get_json(cls, key):
        value = cls._get_value(key)
        if value is not None:
            value = json.loads(value)
        return value

    @classmethod
    def init_cache(cls):
        if cls._connection is not None:
            return cls._connection is not DISABLED_STATE
        redis_db = settings["WIKI_CACHE_REDIS_DB"]
        try:
            redis_pool = get_redis_pool(db=redis_db)
        except RedisNotConfigured:
            logger.warning("No Redis URL has been set for caching", exc_info=True)
            cls._connection = DISABLED_STATE
            return False
        else:
            cls._connection = Redis(connection_pool=redis_pool)
            return True

    @classmethod
    def cache_it(cls, key, f, expire=settings["WIKI_CACHE_TIMEOUT"]):
        """
        Takes function f and put its result in a redis cache.
        It requires a prefix string to identify the name
        of the function cached.
        """
        if cls._connection is None:
            cls.init_cache()

        def with_cache(*args, **kwargs):
            """
            If the redis is up we use the cache,
            otherwise we bypass it
            """
            if cls._connection is not DISABLED_STATE:
                try:
                    value_stored = cls._get_value(key)
                except CacheNotAvailable:
                    # Cache is not reachable: we don't want to execute 'f'
                    # (and fetch remote content, possibly very often)
                    logger.warning("Failed to get cached value for %s", key, exc_info=True)
                    return None
                if value_stored is not None:
                    return json.loads(value_stored.decode("utf-8"))
                result = f(*args, **kwargs)
                json_result = json.dumps(result)
                cls._set_value(key, json_result, expire)
                return result
            return f(*args, **kwargs)

        return with_cache

    @classmethod
    def disable(cls):
        cls._connection = DISABLED_STATE

    @classmethod
    def enable(cls):
        cls._connection = None
        cls.init_cache()


class RedisWrapperWeather(RedisWrapper):
    _redis = RedisWrapper

    @classmethod
    def cache_it(cls, key, f, expire=settings["WEATHER_CACHE_TIMEOUT"]):
        return cls._redis.cache_it(key, f, expire)
