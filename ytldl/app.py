import argparse
import os
from pathlib import Path

from ytldl.yt.cache import SqliteCache
from ytldl.yt.download import Downloader, LibDownloader
from ytldl.yt.oauth import Oauth


def parse_args() -> argparse.Namespace:
    """Returns:
    Namespace(action='dl', dir='d:\\tmp', v=None, l='abc')
    Namespace(action='auth', headers='my heders')
    """

    parser = argparse.ArgumentParser(
        description="Program to download songs and playlists from youtube.")
    action_parsers = parser.add_subparsers(dest="action")
    action_parsers.required = True
    action_parsers.choices = ["dl", "lib"]

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
    lib_action_parsers.choices = ["update", "fix"]

    lib_action_update_parser = lib_action_parsers.add_parser(
        "update")
    lib_action_update_parser.add_argument(
        "-n", "--limit", help="Limit of downloaded tracks per playlist or channel", default=50, type=int)
    lib_action_update_parser.add_argument(
        "--reset_oauth", help="Resets oauth info and forces user to redo authentication", action="store_true")
    lib_action_update_parser.add_argument(
        "-p", "--password", help="Provides password for storing oauth data locally", default=None, type=str)

    lib_action_parsers.add_parser("fix", description="Try to fix lib. For now, fixes only downloaded column")

    res = parser.parse_args()

    res.debug = "DEBUG" in os.environ

    return res


def main():
    args = parse_args()

    match args.action:
        case 'dl':
            cwd_dir = Path(args.dir)
            d = Downloader(cwd_dir, debug=args.debug)
            d.download(videos=args.v, playlists=args.l, channels=args.c)

        case 'lib':
            cwd_dir = Path(args.dir)
            ytldl_dir = cwd_dir / ".ytldl"
            ytldl_dir.mkdir(parents=True, exist_ok=True)
            sqlite_path = cwd_dir / ".ytldl" / "ytldl.db"
            oauth_path = cwd_dir / ".ytldl" / "oauth"
            salt_path = cwd_dir / ".ytldl" / "salt"

            match args.lib_action:
                case 'update':
                    if args.reset_oauth:
                        oauth_path.unlink(missing_ok=True)
                        salt_path.unlink(missing_ok=True)

                    oauth = Oauth(oauth_path, salt_path, password=args.password)
                    d = LibDownloader(cwd_dir, oauth, debug=args.debug,
                                      cache=SqliteCache(str(sqlite_path), batch_size=10))
                    d.lib_update(limit=args.limit)

                case 'fix':
                    d = Downloader(cwd_dir)
                    video_ids = d.get_downloaded_video_ids()
                    print(f"Extracted {len(video_ids)} videoIds from {cwd_dir}")
                    cache = SqliteCache(str(sqlite_path))
                    cache.fix_downloaded_column(video_ids)
                    print(f"Downloaded column fixed for {sqlite_path}")

                    uncached = cache.filter_uncached(video_ids)
                    uncached_str = "\n".join(uncached)
                    print(f"Warning: you have {len(uncached)} uncached songs:\n{uncached_str}")


if __name__ == "__main__":
    main()
