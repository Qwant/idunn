from dataclasses import dataclass
from functools import lru_cache, wraps
from time import monotonic_ns
from typing import Tuple


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
        delta = delta_seconds * 10 ** 9  # nanoseconds

        # Convert parameters to tuples to allow hashing
        args = tuple(args)
        kwargs = tuple(kwargs.items())

        # Previous timestamp multiple of `delta`, this value changes
        # periodicaly in time so that older keys won't be used anymore
        rounded = (monotonic_ns() // delta) * delta

        # Added offset in [0, delta[ to desynchronize cache expiration of different keys
        offset = (delta * (hash((args, kwargs)) + 2 ** 63)) // 2 ** 64

        return cls(rounded + offset, args, kwargs)


def lru_cache_with_expiration(
    func=None,
    *,
    seconds: int,
    maxsize: int = 128,
    typed: bool = False,
):
    """
    Extension over existing lru_cache with per-key timeout. Each key will
    expire, note the delay is not aligned with the first insertion of the key,
    so the cache can be reseted sooner than expected.

    :param seconds: timeout value
    :param maxsize: maximum size of the cache
    :param typed: whether different keys for different types of cache keys

    Some inspiration has been taken from this thread:
    https://gist.github.com/Morreski/c1d08a3afa4040815eafd3891e16b945?permalink_comment_id=3521580#gistcomment-3521580
    """
    if maxsize is None:
        raise Exception(
            "using an unbounded `lru_cache_with_expiration` would result in a memory leak"
        )

    def wrapper_cache(f):
        # Wrap the function to accept its parameters wrapped with a timestamp.
        def func_with_timestamp(key: _CacheKey):
            return f(*key.args, **dict(key.kwargs))

        # Cached version of the function using the new `CacheKey` parameter
        func_with_cache = lru_cache(maxsize=maxsize, typed=typed)(func_with_timestamp)

        @wraps(f)
        def wrapped_func(*args, **kwargs):
            key = _CacheKey.from_args(list(args), kwargs, seconds)
            return func_with_cache(key)

        return wrapped_func

    # Allows decorator to be used without arguments
    if func is None:
        return wrapper_cache

    return wrapper_cache(func)
