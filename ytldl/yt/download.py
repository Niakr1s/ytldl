import pathlib
from asyncio import Future
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable

from yt_dlp import YoutubeDL
from ytmusicapi import YTMusic

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

    def __init__(self, download_dir: str, /, yt: YTMusic = YTMusic(), debug: bool = False):
        self.yt = yt
        self.extractor = Extractor(yt)
        self.debug = debug
        self.set_download_dir(download_dir)

    def set_download_dir(self, download_dir: str):
        pathlib.Path(download_dir).mkdir(parents=True, exist_ok=True)
        if 'paths' not in self._ydl_opts:
            self._ydl_opts['paths'] = {}
        self._ydl_opts['paths']['home'] = download_dir

    # returns download filepath

    def download_track(self, video_id: str) -> str:
        """
        Raises FilterPPException if got filtered.
        Returns videoId of downloaded track (same as input video_id).
        """

        url = Downloader.to_url(video_id)

        if self.debug:
            return video_id

        with YoutubeDL(self._ydl_opts) as ydl:
            ydl.add_post_processor(FilterPP(), when='pre_process')
            ydl.add_post_processor(LyricsPP(), when='post_process')
            ydl.add_post_processor(MetadataPP(), when='post_process')

            ydl.download([url])
            return video_id

    def to_url(video_id: str) -> str:
        return f"https://youtube.com/watch?v={video_id}"

    def download_tracks(self, videos: Iterable[str],
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
                    self.download_track, video_id)
                future.video_id = video_id
                futures.append(future)

            for future in futures:
                video_id: str = future.video_id
                try:
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
        tracks_to_download = self.extractor.extract(
            videos=videos, playlists=playlists, channels=channels, limit=limit)

        downloaded_tracks = self.download_tracks(
            tracks_to_download, *args, **kwargs)
        return downloaded_tracks


class CacheDownloader(Downloader):
    def __init__(self, download_dir: str, /, cache: Cache = MemoryCache(), *args, **kwargs):
        super().__init__(download_dir, *args, **kwargs)
        self.cache = cache

    def download_tracks(self, videos: Iterable[str], **kwargs) -> Iterable[str]:
        uncached_video_ids = self.cache.filter_uncached(videos)
        print(f"download only uncached {len(uncached_video_ids)} tracks")

        downloaded_tracks = super().download_tracks(
            uncached_video_ids,
            after_download=lambda x: self.cache.add_items([x]),
            on_discarded=lambda x: self.cache.add_items(x))
        self.cache.commit()
        return downloaded_tracks


class LibDownloader(CacheDownloader):
    def __init__(self, download_dir: str, *args, **kwargs):
        super().__init__(download_dir, *args, **kwargs)

    def get_home_items(self, filter_titles: list[str]) -> dict:
        """
        Returns home items in format of { videos, playlists, channels },
            that can be put into download function
        """
        home = self.yt.get_home(limit=10)
        if filter_titles:
            home = [chapter for chapter in home if chapter["title"] in filter_titles]

        home_items = [
            contents for home_item in home for contents in home_item["contents"]]

        res = dict(videos=[], playlists=[], channels=[])
        for home_item in home_items:
            if "videoId" in home_item:
                res['videos'].append(home_item["videoId"])
            if "subscribers" in home_item and "browseId" in home_item:
                res['channels'].append(home_item["browseId"])
            if "playlistId" in home_item:
                res["playlists"].append(home_item["playlistId"])
        return res

    personalised_home_titles = ["Listen again", "Mixed for you: moods",
                                "Quick picks", "Mixed for you", "Forgotten favorites"]

    def lib_update(self, limit: int = 50):
        print("Starting updating lib...")
        home_items = self.get_home_items(
            filter_titles=self.personalised_home_titles)

        downloaded_tracks = list(self.download(**home_items, limit=limit))
        print(f"Downloaded {sum(1 for i in downloaded_tracks)} tracks")
