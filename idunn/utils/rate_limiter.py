import logging
from apistar.exceptions import HTTPException
from contextlib import contextmanager
from redis import RedisError
from redis_rate_limit import RateLimiter, TooManyRequests
from idunn.utils.redis import get_redis_pool, RedisNotConfigured
from idunn import settings

logger = logging.getLogger(__name__)

TooManyRequestsException = TooManyRequests

@contextmanager
def dummy_limit():
    yield

class HTTPTooManyRequests(HTTPException):
    default_status_code = 429
    default_detail = 'Too Many Requests'

class IdunnRateLimiter:
    def __init__(self, resource, max_requests, expire):
        self.resource = resource
        self.max_requests = max_requests
        self.expire = expire
        self._init_limiter()

    def _init_limiter(self):
        try:
            redis_pool = get_redis_pool(db=settings['RATE_LIMITER_REDIS_DB'])
        except RedisNotConfigured:
            logger.warning("Redis URL not configured: rate limiter not started")
            self._limiter = None
        else:
            """
            If a redis is configured,
            then we use the corresponding redis
            service in the rate limiter.
            """
            self._limiter = RateLimiter(
                resource=self.resource,
                max_requests=self.max_requests,
                expire=self.expire,
                redis_pool=redis_pool
            )

    def limit(self, client, ignore_redis_error=False):
        if self._limiter is None:
            return dummy_limit()

        @contextmanager
        def limit():
            try:
                with self._limiter.limit(client):
                    yield
            except RedisError as e:
                if ignore_redis_error:
                    logger.warning(
                        'Ignoring RedisError in rate limiter for %s',
                        self._limiter.resource, exc_info=True
                    )
                    yield
                else:
                    raise

        return limit()

    def check_limit_per_client(self, request):
        client_id = request.headers.get('x-client-hash') or 'default'
        try:
            with self.limit(client=client_id, ignore_redis_error=True):
                pass
        except TooManyRequestsException:
            raise HTTPTooManyRequests
