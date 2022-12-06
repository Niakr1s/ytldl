import pathlib
import signal
from asyncio import Future
from concurrent.futures import ThreadPoolExecutor
from os import PathLike
from time import sleep
from typing import Callable, Iterable

from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

from ytldl.util.url import to_url
from ytldl.yt.cache import Cache, MemoryCache
from ytldl.yt.extractor import Extractor
from ytldl.yt.postprocessors import FilterPP, FilterPPException, LyricsPP, MetadataPP


class Downloader:
    """
    Downloads tracks.

    First we should setup auth headers:
       Downloader.setup(auth_header_path, headers_raw)

    Instantiate downloader instance:
       d = Downloader(download_dir=dir, auth_header_path)

    Download.
     :v
      VIDEO param video page's url:  https://music.youtube.com/watch?v=VIDEO
     :l
      LIST param of playlist page's url: https://music.youtube.com/playlist?list=LIST
     :c
      CHANNEL param of artist page's url: https://music.youtube.com/channel/CHANNEL
       d.download(v=args.v, l=args.l, c=args.c)
    """

    _ydl_opts = {
        'format': 'bestaudio/best',
        # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
        'postprocessors': [
            {  # Extract audio using ffmpeg
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            },
        ],
        'outtmpl': {
            'default': '%(artist).20s - %(title).50s [%(id)s].%(ext)s',
        },
    }

    def __init__(self, download_dir: PathLike, /, yt: YTMusic = YTMusic(), debug: bool = False):
        self._stopped = False
        self._yt = yt
        self._extractor = Extractor(yt)
        self._debug = debug
        self._set_download_dir(download_dir)

        signal.signal(signal.SIGINT, lambda *a: self.stop())
        signal.signal(signal.SIGTERM, lambda *a: self.stop())

    def _set_download_dir(self, download_dir: PathLike):
        pathlib.Path(download_dir).mkdir(parents=True, exist_ok=True)
        if 'paths' not in self._ydl_opts:
            self._ydl_opts['paths'] = {}
        self._ydl_opts['paths']['home'] = str(download_dir)

    # returns download filepath

    def _download_track(self, video_id: str) -> str:
        """
        Raises FilterPPException if got filtered.
        Returns videoId of downloaded track (same as input video_id).
        """

        url = to_url(video_id)

        if self._debug:
            sleep(1)
            return video_id

        with YoutubeDL(self._ydl_opts) as ydl:
            ydl.add_post_processor(FilterPP(), when='pre_process')
            ydl.add_post_processor(LyricsPP(), when='post_process')
            ydl.add_post_processor(MetadataPP(), when='post_process')

            ydl.download([url])
            return video_id

    def _download_tracks(self, videos: Iterable[str],
                         after_download: Callable[[str], None] = None,
                         on_discarded: Callable[[Iterable[str]], None] = None) \
            -> Iterable[str]:
        """
        Downloads several tracks, based on their videoIds in thread pool.
        Uses set() to not to allow video_ids duplicates.
        Returns list of downloaded tracks.
        """

        downloaded_videos = []
        videos = set(videos)
        with ThreadPoolExecutor() as executor:
            futures: list[Future] = []
            for video_id in videos:
                future = executor.submit(
                    self._download_track, video_id)
                future.video_id = video_id
                futures.append(future)

            for future in futures:
                video_id: str = future.video_id
                try:
                    if self._stopped:
                        executor.shutdown(wait=True, cancel_futures=True)

                    future.result()
                    if after_download:
                        after_download(video_id)
                    downloaded_videos.append(video_id)
                except FilterPPException:
                    print(f"discarding {video_id} due to FilterPP")
                    if on_discarded:
                        on_discarded([video_id])
                except Exception as e:
                    print(f"couldn't download {video_id}: {e}")
        return iter(downloaded_videos)

    def download(self,
                 videos: Iterable[str] = None,
                 playlists: Iterable[str] = None,
                 channels: Iterable[str] = None,
                 limit: int = 50, *args, **kwargs):
        """
        Main method of this class.
        Limit is max tracks per list or channel.
        """
        self._stopped = False

        tracks_to_download = self._extractor.extract(
            videos=videos, playlists=playlists, channels=channels, limit=limit)

        downloaded_tracks = self._download_tracks(
            tracks_to_download, *args, **kwargs)
        return downloaded_tracks

    def stop(self):
        print("STOPPING...")
        self._stopped = True


class CacheDownloader(Downloader):
    def __init__(self, download_dir: PathLike, /, cache: Cache = MemoryCache(), *args, **kwargs):
        super().__init__(download_dir, *args, **kwargs)
        self._cache = cache

    def _download_tracks(self, videos: Iterable[str], **kwargs) -> Iterable[str]:
        uncached_video_ids = self._cache.filter_uncached(videos)
        print(f"download only uncached {len(uncached_video_ids)} tracks")

        downloaded_tracks = super()._download_tracks(
            uncached_video_ids,
            after_download=lambda x: self._cache.add_items([x]),
            on_discarded=lambda x: self._cache.add_discarded_items(x))
        self._cache.commit()
        return downloaded_tracks


class LibDownloader(CacheDownloader):
    def __init__(self, download_dir: PathLike, *args, **kwargs):
        super().__init__(download_dir, *args, **kwargs)

    # TODO: add to settings etc
    _personalised_home_titles = [
        # "Listen again", # I don't like "Listen again" section, coz it's download too much monotonous music.
        "Mixed for you: moods",
        "Quick picks",
        "Mixed for you",
        "Forgotten favorites",
    ]

    _skip_home_title_items = [
        'Discover Mix',
        'Your Likes',
        'Replay Mix',
        'New Release Mix',
    ]

    def _get_home_items(self, filter_titles: list[str]) -> dict:
        """
        Returns home items in format of { videos, playlists, channels },
            that can be put into download function
        """
        home = self._yt.get_home(limit=100)
        if filter_titles:
            home = [chapter for chapter in home if chapter["title"]
                    in filter_titles]

        home_items = [
            contents for home_item in home for contents in home_item["contents"]]

        res = dict(videos=[], playlists=[], channels=[])
        for home_item in home_items:
            title = home_item["title"]

            if "subscribers" in home_item and "browseId" in home_item:
                browse_id = home_item["browseId"]
                print(f"Appending channel {title} with browseId {browse_id}")
                res['channels'].append(browse_id)
                continue

            video_id = home_item.get("videoId", None)
            playlist_id = home_item.get("playlistId", None)
            if video_id:
                print(f"Appending video {title} with videoId {video_id}")
                res['videos'].append(video_id)
            if playlist_id:
                if title in self._skip_home_title_items:
                    print(f"Skipping playlist {title} with playlist_id {playlist_id}")
                    continue
                print(f"Appending playlist {title} with playlist_id {playlist_id}")
                res["playlists"].append(playlist_id)
        return res

    def lib_update(self, limit: int = 50):
        print("Starting updating lib...")
        home_items = self._get_home_items(
            filter_titles=self._personalised_home_titles)

        downloaded_tracks = list(self.download(**home_items, limit=limit))
        print(f"Downloaded {sum(1 for i in downloaded_tracks)} tracks")
