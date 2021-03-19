import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app import app
from idunn.utils.ban_check import get_ban_check_http
from tests.utils import override_settings


@pytest.fixture
def enable_bancheck(httpx_mock):
    with override_settings(
        {
            "BANCHECK_ENABLED": True,
            "QWANT_API_BASE_URL": "http://qwant-api.test",
        }
    ), patch("idunn.utils.ban_check.ban_check_http", new_callable=get_ban_check_http):
        httpx_mock.get(url__regex=r"http://qwant-api.test/v3/captcha/isban.*").respond(
            json={"status": "success", "data": True}
        )
        yield


def test_ia_client_banned(enable_bancheck):
    client = TestClient(app)
    response = client.get(
        "/v1/instant_answer",
        params={"q": "paris", "lang": "fr"},
        headers={"x-client-hash": "banned"},
    )
    assert response.status_code == 429
