import pybreaker
import logging
from requests import HTTPError

from idunn import settings

logger = logging.getLogger(__name__)


def is_http_client_error(exc):
    return (
        isinstance(exc, HTTPError)
        and exc.response is not None
        and 400 <= exc.response.status_code < 500
    )


class LogListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        msg = "State Change: CB: {0}, From: {1} to New State: {2}".format(
            cb.name, old_state, new_state
        )
        logger.warning(msg)


class IdunnCircuitBreaker(pybreaker.CircuitBreaker):
    def __init__(self, name):
        super().__init__(
            fail_max=settings["CIRCUIT_BREAKER_MAXFAIL"],
            reset_timeout=settings["CIRCUIT_BREAKER_TIMEOUT"],
            exclude=[is_http_client_error],
            listeners=[LogListener()],
            name=name,
        )

    async def call_async(self, f, *args, **kwargs):
        """
        Run the circuit breaker with native python async.
        """

        def raise_err_callback(err):
            def f():
                raise err

            return f

        # Check that the circuit breaker is open
        state = self.state

        if isinstance(state, pybreaker.CircuitOpenState):
            # This is a hack: `before_call` takes a function parameter that
            # should not be used, this way we can reproduce synchronous
            # behavior before running the function by raising the exact same
            # exception.
            state.before_call(None)

        # Build a synchronous `callback` function that simulates the return
        # behaviour of `f`.
        try:
            res = await f(*args, **kwargs)
            callback = lambda: res
        except Exception as err:
            callback = raise_err_callback(err)

        return self.call(callback)
