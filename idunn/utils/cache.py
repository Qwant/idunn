from collections import OrderedDict
from dataclasses import dataclass
from functools import wraps
from time import monotonic_ns
from typing import Generic, TypeVar


# pylint: disable = invalid-name
K, V = TypeVar("K"), TypeVar("V")


@dataclass
class _CacheTsValue(Generic[V]):
    value: V
    timestamp: int


class TimedLRUCache(Generic[K, V]):
    """
    Basic LRU cache which handles timed expiration, backed with an OrderedDict.
    """

    def __init__(self, maxsize: int, seconds: float):
        self.cache = OrderedDict()
        self.capacity = maxsize
        self.ttl = int(seconds * 10 ** 9)  # nanoseconds

    def _is_expired(self, key: K) -> bool:
        return self.cache[key].timestamp + self.ttl >= monotonic_ns()

    def get(self, key: K) -> V:
        if key not in self.cache or self._is_expired(key):
            raise IndexError

        self.cache.move_to_end(key, last=False)  # moves key at the beginning
        return self.cache[key].value

    def put(self, key: K, value: V):
        self.cache[key] = _CacheTsValue(value, monotonic_ns())

        if len(self.cache) > self.capacity:
            self.cache.popitem()


def async_timed_lru_cache(
    func=None,
    *,
    seconds: float,
    maxsize: int = 128,
):
    """
    Extension over existing lru_cache with per-key timeout. Each key will
    expire with a delay of `seconds` after its last computation.

    :param seconds: timeout value
    :param maxsize: maximum size of the cache

    Some inspiration has been taken from this thread:
    https://gist.github.com/Morreski/c1d08a3afa4040815eafd3891e16b945?permalink_comment_id=3521580#gistcomment-3521580
    """
    cache = TimedLRUCache(maxsize, seconds)

    def wrapper_cache(f):
        @wraps(f)
        async def wrapped_func(*args, **kwargs):
            key = (tuple(args), tuple(kwargs.items()))

            try:
                res = cache.get(key)
            except IndexError:
                res = await f(*args, **kwargs)
                cache.put(key, res)

            return res

        return wrapped_func

    # Allows decorator to be used without arguments
    if func is None:
        return wrapper_cache

    return wrapper_cache(func)
