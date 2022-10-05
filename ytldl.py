import argparse
import pathlib
from random import choices
from typing import Dict
from yt.cache import MemoryCache, SqliteCache
from yt.download import Downloader, LibDownloader
import os


def args() -> argparse.Namespace:
    """Returns:
    Namespace(action='dl', dir='d:\\tmp', v=None, l='abc')
    Namespace(action='auth', headers='my heders')
    """

    parser = argparse.ArgumentParser(
        description="Programm to download songs and playlists from youtube.")
    action_parsers = parser.add_subparsers(dest="action")
    action_parsers.required = True
    action_parsers.choices = ["auth", "dl", "lib"]

    # AUTH
    auth_parser = action_parsers.add_parser("auth")
    auth_parser.add_argument("headers", help="""How to get headers:
    Open a new tab.
    Open the developer tools (Ctrl-Shift-I) and select the “Network” tab. 
    Go to https://music.youtube.com and ensure you are logged in. 
    Find an authenticated POST request. The simplest way is to filter by /browse using the search bar of the developer tools. If you don’t see the request, try scrolling down a bit or clicking on the library button in the top bar. 

    Firefox

        Verify that the request looks like this: Status 200, Method POST, Domain music.youtube.com, File browse?...
        Copy the request headers (right click > copy > copy request headers)

    Chromium (Chrome/Edge)

        Verify that the request looks like this: Status 200, Name browse?...
        Click on the Name of any matching request. In the “Headers” tab, scroll to the section “Request headers” and copy everything starting from “accept: */*” to the end of the section

    Then paste these headers here (surround with quotes: "YOUR HEADERS HERE").""")

    # DL
    dl_parser = action_parsers.add_parser("dl")
    dl_parser.add_argument(
        "-o", "--dir", help="output directory", required=True)
    group = dl_parser.add_argument_group()
    group.required = True
    group.add_argument(
        "-v",  help="Video from song page: https://music.youtube.com/watch?v=VIDEO", nargs='*', default=[])
    group.add_argument(
        "-l", help="List from playlist page: https://music.youtube.com/playlist?list=LIST", nargs='*', default=[])
    group.add_argument(
        "-c",  help="Video from channel page: https://music.youtube.com/channel/CHANNEL", nargs='*', default=[])

    # LIB
    lib_parser = action_parsers.add_parser("lib")
    lib_parser.add_argument(
        "-o", "--dir", help="sets output directory", required=True)

    lib_action_parsers = lib_parser.add_subparsers(dest="lib_action")
    lib_action_parsers.required = True
    lib_action_parsers.choices = ["update"]

    lib_action_update_parser = lib_action_parsers.add_parser(
        "update")
    lib_action_update_parser.add_argument(
        "-n", "--limit", help="Limit of downloaded tracks", default=0, type=int)

    res = parser.parse_args()

    res.debug = "DEBUG" in os.environ

    return res


def make_settings_dir() -> str:
    settings_dir = pathlib.Path.home() / ".ytldl"
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir


if __name__ == "__main__":
    args = args()
    settings_dir = make_settings_dir()
    auth_header_path = settings_dir / "auth_headers.json"

    match args.action:
        case 'dl':
            dir = args.dir
            d = Downloader(download_dir=dir,
                           auth=settings_dir / auth_header_path, debug=args.debug)
            d.download(v=args.v, l=args.l, c=args.c)

        case 'auth':
            headers_raw = args.headers
            Downloader.setup(
                settings_dir / auth_header_path, headers_raw)

        case 'lib':
            dir = args.dir
            ytldl_dir = pathlib.Path(dir) / ".ytldl"
            ytldl_dir.mkdir(parents=True, exist_ok=True)
            sqlite_path = pathlib.Path(dir) / ".ytldl" / "ytldl.db"

            if not sqlite_path.exists():
                SqliteCache.create(sqlite_path)

            match args.lib_action:
                case 'update':
                    d = LibDownloader(download_dir=dir,
                                      auth=settings_dir / auth_header_path, debug=args.debug, cache=SqliteCache(str(sqlite_path), batch_size=100))
                    d.lib_update(limit=args.limit)
