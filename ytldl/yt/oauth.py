import json
import os
import pathlib
from os import PathLike

import robocrypt
import ytmusicapi
from robocrypt import encrypt, decrypt


class Oauth:
    def __init__(self, oauth_path: PathLike, salt_path: PathLike, /, password: str | None = None) -> None:
        self._oauth_path = pathlib.Path(oauth_path)
        if password is None:
            password = Oauth._ask_password()

        salt_path = pathlib.Path(salt_path)
        os.environ['ROBO_SALT_FILE'] = str(salt_path.as_posix())
        if not salt_path.exists():
            robocrypt.generate_salt(10)

        self._password = password.encode()

    @staticmethod
    def _ask_password() -> str:
        return input("enter password for encrypt oauth file: ").strip()

    @property
    def auth(self) -> str:
        if self._oauth_path.exists():
            return self._load()

        headers = ytmusicapi.setup_oauth()
        contents = json.dumps(headers)
        self._dump(contents)
        return contents

    def _load(self) -> str:
        contents = self._oauth_path.read_bytes()
        decrypted = decrypt(contents, self._password).decode()
        return decrypted

    def _dump(self, contents: str):
        encrypted = encrypt(contents.encode(), self._password)
        self._oauth_path.write_bytes(encrypted)
