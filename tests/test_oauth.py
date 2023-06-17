import json
import pathlib
from unittest import TestCase

from ytldl.yt.oauth import Oauth


class TestOauth(TestCase):
    def setUp(self) -> None:
        self.path = pathlib.Path("oauth_tmp")
        self.path.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.path.unlink(missing_ok=True)

    def test_auth_with_password(self):
        self._test_auth("123")

    def test_auth_without_password(self):
        self._test_auth(None)

    def _test_auth(self, password: str | None):
        path = pathlib.Path("oauth_tmp")
        oauth = Oauth(path, password)
        self.assertEqual(False, path.exists())

        headers1 = oauth.auth
        self.assertEqual(True, path.exists())
        self.assertEqual(True, isinstance(headers1, str))
        self.assertEqual(True, "access_token" in json.loads(headers1))

        headers2 = oauth.auth
        self.assertEqual(headers1, headers2)
