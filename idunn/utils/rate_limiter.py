import logging
from fastapi import HTTPException, Depends, Request
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


try:
    redis_pool = get_redis_pool(db=settings["RATE_LIMITER_REDIS_DB"])
except RedisNotConfigured:
    logger.warning("Redis URL not configured: rate limiter not started")
    redis_pool = None


class IdunnRateLimiter:
    def __init__(self, resource, max_requests, expire):
        self.resource = resource
        self.max_requests = max_requests
        self.expire = expire
        self._init_limiter()

    def _init_limiter(self):
        if redis_pool:
            # If a redis is configured, then we use the corresponding redis service in the rate
            # limiter.
            self._limiter = RateLimiter(
                resource=self.resource,
                max_requests=self.max_requests,
                expire=self.expire,
                redis_pool=redis_pool,
            )
        else:
            self._limiter = None

    def limit(self, client, ignore_redis_error=False):
        # Handle lazy initialization of the redis pool for test context
        if (redis_pool is None) ^ (self._limiter is None):
            self._init_limiter()

        if self._limiter is None:
            return dummy_limit()

        @contextmanager
        def limit():
            try:
                with self._limiter.limit(client):
                    yield
            except RedisError:
                if ignore_redis_error:
                    logger.warning(
                        "Ignoring RedisError in rate limiter for %s",
                        self._limiter.resource,
                        exc_info=True,
                    )
                    yield
                else:
                    raise

        return limit()

    def check_limit_per_client(self, request):
        client_id = request.headers.get("x-client-hash")

        if client_id is None:
            logger.warning("Ignoring rate limiting for request with no hash")
            return

        try:
            with self.limit(client=client_id, ignore_redis_error=True):
                pass
        except TooManyRequestsException as exc:
            raise HTTPException(status_code=429, detail="Too Many Requests") from exc


def rate_limiter_dependency(**kwargs):
    rate_limiter = IdunnRateLimiter(**kwargs)

    def dependency(request: Request):
        rate_limiter.check_limit_per_client(request)

    return Depends(dependency)
