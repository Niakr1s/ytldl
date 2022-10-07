import argparse
import os
from pathlib import Path

from ytmusicapi import YTMusic

from ytldl.yt.cache import SqliteCache
from ytldl.yt.download import Downloader, LibDownloader


def parse_args() -> argparse.Namespace:
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
    auth_parser.add_argument("headers", help="""How to get headers: Open a new tab. Open the developer tools ( 
    Ctrl-Shift-I) and select the “Network” tab. Go to https://music.youtube.com and ensure you are logged in. Find an 
    authenticated POST request. The simplest way is to filter by /browse using the search bar of the developer tools. 
    If you don’t see the request, try scrolling down a bit or clicking on the library button in the top bar. 

    Firefox

        Verify that the request looks like this: Status 200, Method POST, Domain music.youtube.com, File browse?...
        Copy the request headers (right click > copy > copy request headers)

    Chromium (Chrome/Edge)

        Verify that the request looks like this: Status 200, Name browse?... Click on the Name of any matching 
        request. In the “Headers” tab, scroll to the section “Request headers” and copy everything starting from 
        “accept: */*” to the end of the section 

    Then paste these headers here (surround with quotes: "YOUR HEADERS HERE").""")

    # DL
    dl_parser = action_parsers.add_parser("dl")
    dl_parser.add_argument(
        "-o", "--dir", help="output directory", required=True)
    group = dl_parser.add_argument_group()
    group.required = True
    group.add_argument(
        "-v", help="Video from song page: https://music.youtube.com/watch?v=VIDEO", nargs='*', default=[])
    group.add_argument(
        "-l", help="List from playlist page: https://music.youtube.com/playlist?list=LIST", nargs='*', default=[])
    group.add_argument(
        "-c", help="Video from channel page: https://music.youtube.com/channel/CHANNEL", nargs='*', default=[])

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
        "-n", "--limit", help="Limit of downloaded tracks per playlist or channel", default=50, type=int)

    res = parser.parse_args()

    res.debug = "DEBUG" in os.environ

    return res


def make_settings_dir() -> Path:
    settings_dir = Path.home() / ".ytldl"
    settings_dir.mkdir(parents=True, exist_ok=True)
    return settings_dir


def main():
    args = parse_args()
    settings_dir = make_settings_dir()
    auth_header_path = settings_dir / "auth_headers.json"
    auth_dir = settings_dir / auth_header_path

    match args.action:
        case 'dl':
            yt = YTMusic(auth=str(auth_dir))
            cwd_dir = Path(args.dir)
            d = Downloader(cwd_dir, yt=yt, debug=args.debug)
            d.download(videos=args.v, playlists=args.l, channels=args.c)

        case 'auth':
            headers_raw = args.headers
            YTMusic.setup(str(auth_dir), headers_raw)

        case 'lib':
            yt = YTMusic(auth=str(auth_dir))
            cwd_dir = Path(args.dir)
            ytldl_dir = cwd_dir / ".ytldl"
            ytldl_dir.mkdir(parents=True, exist_ok=True)
            sqlite_path = cwd_dir / ".ytldl" / "ytldl.db"

            if not sqlite_path.exists():
                SqliteCache.create(sqlite_path)

            match args.lib_action:
                case 'update':
                    d = LibDownloader(download_dir=cwd_dir, yt=yt, debug=args.debug,
                                      cache=SqliteCache(str(sqlite_path), batch_size=10))
                    d.lib_update(limit=args.limit)


if __name__ == "__main__":
    main()
