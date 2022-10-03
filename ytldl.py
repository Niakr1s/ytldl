import argparse
import pathlib
from random import choices
from typing import Dict
from yt.download import Downloader


def args() -> argparse.Namespace:
    """Returns:
    Namespace(action='dl', dir='d:\\tmp', v=None, l='abc')
    Namespace(action='auth', headers='my heders')
    """

    parser = argparse.ArgumentParser(
        description="Programm to download songs and playlists from youtube.")
    action_parsers = parser.add_subparsers(dest="action")
    action_parsers.required = True
    action_parsers.choices = ["auth", "dl"]

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
    group = dl_parser.add_mutually_exclusive_group()
    group.required = True
    group.add_argument(
        "-v",  help="Video from song page: https://music.youtube.com/watch?v=VIDEO")
    group.add_argument(
        "-l", help="List from playlist page: https://music.youtube.com/playlist?list=LIST")

    res = parser.parse_args()
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
                           auth=settings_dir / auth_header_path)
            if args.v:
                d.download_track(args.v)
            elif args.l:
                d.download_playlist(args.l)

        case 'auth':
            headers_raw = args.headers
            Downloader.setup(
                settings_dir / auth_header_path, headers_raw)
