import re
from functools import wraps
import responses


def mock_wikipedia_with_404(test_fun):
    @wraps(test_fun)
    def wrapper(*args, **kwargs):
        with responses.RequestsMock() as rsps:
            rsps.add('GET',
                     re.compile('^https://.*\.wikipedia.org/'),
                     status=404)
            return test_fun(*args, **kwargs)
    return wrapper
