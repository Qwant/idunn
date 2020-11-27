from time import time

import logging
import requests


class AuthSession:
    """
    Helper class for HTTP sessions that need to keep an authentification token.
    Default behavior corresponds to an OAuth2 API.

    Note that at least `get_authorization_url` and `get_authorization_params`
    need to be overriden.
    """

    def __init__(self, expiration_tolerance=10, refresh_timeout=1000):
        self.inner = requests.Session()
        self.expiration_tolerance = expiration_tolerance
        self.refresh_timeout = refresh_timeout
        self.token_expires_at = 0

    def get_authorization_url(self) -> str:
        raise NotImplementedError

    def get_authorization_params(self) -> dict:
        raise NotImplementedError

    @staticmethod
    def parse_authorisation_response(resp: dict) -> (str, int):
        """
        Build the token and the expiration date timestamp from the response
        from authorization API.
        """
        token = resp["access_token"]
        expires_at = int(resp["issued_at"]) + int(resp["expires_in"])
        return token, expires_at

    def query_new_token(self) -> requests.Response:
        """Perform a query to the authorization API"""
        return self.inner.post(
            self.get_authorization_url(),
            data=self.get_authorization_params(),
            timeout=self.refresh_timeout,
        )

    def get_new_token(self):
        """Get a new token"""
        logging.info(
            "token expired at %s, querying a new one from %s",
            self.token_expires_at,
            self.get_authorization_url(),
        )
        resp = self.query_new_token()
        resp.raise_for_status()

        token, self.token_expires_at = self.parse_authorisation_response(resp.json())
        self.inner.headers["Authorization"] = f"Bearer {token}"

    def refresh_token(self):
        """Get a new token if current one is expired"""
        if self.token_expires_at - time() < self.expiration_tolerance:
            self.inner.headers.pop("Authorization", None)
            self.get_new_token()

    def get(self, *args, **kwargs):
        self.refresh_token()
        return self.inner.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self.refresh_token()
        return self.inner.post(*args, **kwargs)
