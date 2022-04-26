from collections import OrderedDict
from dataclasses import dataclass
from functools import lru_cache, wraps
from time import monotonic_ns
from typing import Generic, Optional, Tuple, TypeVar


@dataclass(eq=True, frozen=True)
class _CacheKey:
    """
    Wrap function parameters together with a time point, this is used as a
    replacement to parameters of a function in order to simulate expiration in
    a lru cache.
    """

    timestamp: int
    args: Tuple
    kwargs: Tuple

    @classmethod
    def from_args(cls, args: list, kwargs: dict, delta_seconds: int):
        delta = delta_seconds * 10**9  # nanoseconds

        # Convert parameters to tuples to allow hashing
        args = tuple(args)
        kwargs = tuple(kwargs.items())

        # Previous timestamp multiple of `delta`, this value changes
        # periodicaly in time so that older keys won't be used anymore
        rounded = (monotonic_ns() // delta) * delta

        # Added offset in [0, delta[ to desynchronize cache expiration of different keys
        offset = (delta * (hash((args, kwargs)) + 2**63)) // 2**64

        return cls(rounded + offset, args, kwargs)


# pylint: disable = invalid-name
K, V = TypeVar("K"), TypeVar("V")


class LRUCache(Generic[K, V]):
    def __init__(self, maxsize: int):
        self.cache = OrderedDict()
        self.capacity = maxsize

    def contains(self, key: K) -> bool:
        return key in self.cache

    def get(self, key: K) -> V:
        if key not in self.cache:
            raise IndexError

        self.cache.move_to_end(key, last=False) # moves key at the beginning
        return self.cache[key]

    def put(self, key: K, value: V):
        self.cache[key] = value

        if len(self.cache) > self.capacity:
            self.cache.popitem()


def async_lru_cache_with_expiration(
    func=None,
    *,
    seconds: int,
    maxsize: int = 128,
):
    """
    Extension over existing lru_cache with per-key timeout. Each key will
    expire, note the delay is not aligned with the first insertion of the key,
    so the cache can be reseted sooner than expected.

    :param seconds: timeout value
    :param maxsize: maximum size of the cache

    Some inspiration has been taken from this thread:
    https://gist.github.com/Morreski/c1d08a3afa4040815eafd3891e16b945?permalink_comment_id=3521580#gistcomment-3521580
    """
    cache = LRUCache(maxsize)

    def wrapper_cache(f):
        @wraps(f)
        async def wrapped_func(*args, **kwargs):
            key = _CacheKey.from_args(list(args), kwargs, seconds)

            if cache.contains(key):
                return cache.get(key)

            res = await f(*args, **kwargs)
            cache.put(key, res)
            return res

        return wrapped_func

    # Allows decorator to be used without arguments
    if func is None:
        return wrapper_cache

    return wrapper_cache(func)
