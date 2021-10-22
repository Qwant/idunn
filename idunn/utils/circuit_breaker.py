from datetime import datetime, timedelta

import pybreaker
import logging
from requests import HTTPError

logger = logging.getLogger(__name__)


def is_http_client_error(exc):
    return (
        isinstance(exc, HTTPError)
        and exc.response is not None
        and 400 <= exc.response.status_code < 500
    )


class LogListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb, old_state, new_state):
        msg = f"State Change: CB: {cb.name}, From: {old_state} to New State: {new_state}"
        logger.warning(msg)


class IdunnCircuitBreaker(pybreaker.CircuitBreaker):
    def __init__(self, name, fail_max, reset_timeout):
        super().__init__(
            fail_max=int(fail_max),
            reset_timeout=int(reset_timeout),
            exclude=[is_http_client_error],
            listeners=[LogListener()],
            name=name,
        )

    # pylint: disable = arguments-differ, invalid-overridden-method
    async def call_async(self, f, *args, **kwargs):
        """
        Run the circuit breaker with native python async.
        """

        def raise_err_callback(err):
            def f():
                raise err

            return f

        # Check that the circuit breaker is open
        with self._lock:
            state = self.state

            if isinstance(state, pybreaker.CircuitOpenState):
                timeout = timedelta(seconds=state._breaker.reset_timeout)
                opened_at = state._breaker._state_storage.opened_at

                if opened_at and datetime.utcnow() < opened_at + timeout:
                    raise pybreaker.CircuitBreakerError("Timeout not elapsed yet")

                state._breaker.half_open()

            # Build a synchronous `callback` function that simulates the return
            # behaviour of `f`.
            try:
                res = await f(*args, **kwargs)
                callback = lambda: res
            except Exception as err:
                callback = raise_err_callback(err)

            return self.call(callback)
