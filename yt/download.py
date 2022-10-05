from concurrent.futures import Future, ThreadPoolExecutor
from functools import partial
import pathlib
import random
from typing import Any, Callable, Dict, List
from yt_dlp import YoutubeDL
from util.exxception import try_or
from yt.cache import Cache, MemoryCache
from yt.postprocessors import LyricsPP, MetadataPP
from ytmusicapi import YTMusic


class Downloader(YTMusic):
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
            'default': '%(artist).30s - %(title).50s.%(ext)s',
        },
    }

    def __init__(self, download_dir: str, auth: str = None, debug: bool = False):
        super().__init__(auth)
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
            ydl.add_post_processor(LyricsPP(), when='post_process')
            ydl.add_post_processor(MetadataPP(), when='post_process')

            ydl.download([url])
            return video_id

    def filter(self, video_id) -> bool:
        """
        Returns true, if intended to keep.
        """
        def is_song(info: Dict[str, Any]) -> bool:
            return all(k in info for k in ["artist", "title"])

        with YoutubeDL(self._ydl_opts) as ydl:
            info = ydl.extract_info(
                Downloader.to_url(video_id), download=False)
            return is_song(info)

    def to_url(video_id: str) -> str:
        return f"https://youtube.com/watch?v={video_id}"

    def filter_songs(self, video_ids: list[str]) -> tuple[list[str], list[str]]:
        """
        Returns tuple[keeped, discarded]
        """

        keeped = []
        discarded = []
        with ThreadPoolExecutor() as executor:
            futures = {}
            for video_id in video_ids:
                futures[video_id] = future = executor.submit(
                    self.filter, video_id)
            for video_id, future in futures.items():
                try:
                    keep = future.result()
                    if keep:
                        keeped.append(video_id)
                    else:
                        discarded.append(video_id)
                except Exception as e:
                    print(f"couldn't get info {video_id}: {e}")
        print(f"keeped {len(keeped)} out of {len(video_ids)} songs")
        return (keeped, discarded)

    def download_tracks(self, video_ids: List[str],
                        after_download: Callable[[str], None] = None, on_discarded: Callable[[list[str]], None] = None,
                        limit: int = 0) -> list[str]:
        """
        Downloads several tracks, based on their video_ids in thread pool.
        Uses set() to not to allow video_ids doublicates.
        after_download
        Returns list of downloaded tracks.
        """

        video_ids = set(video_ids)
        video_ids, discarded = self.filter_songs(video_ids)
        if on_discarded:
            on_discarded(discarded)

        if limit != 0:
            limit = min(limit, len(video_ids))
            video_ids = random.sample(video_ids, limit)

        downloaded_video_ids = []

        with ThreadPoolExecutor() as executor:
            futures = {}
            for video_id in video_ids:
                futures[video_id] = executor.submit(
                    self.download_track, video_id)
            for video_id, future in futures.items():
                try:
                    future.result()
                    downloaded_video_ids.append(video_id)
                    if after_download:
                        after_download(video_id)
                except Exception as e:
                    print(f"couldn't download {video_id}: {e}")

        return downloaded_video_ids

    def extract_video_ids(self, playlist_id: str) -> List[str]:
        playlist = try_or(
            partial(Downloader.get_playlist, self, playlistId=playlist_id))
        if playlist == None:
            playlist = try_or(
                partial(Downloader.get_watch_playlist, self, playlistId=playlist_id))
        if playlist == None:
            print("couldn't get songs from {}".format(playlist_id))
            return []
        tracks: List[Any] = playlist['tracks']
        print(f"got {len(tracks)} songs from {playlist_id}")
        return map(lambda x: x['videoId'], tracks)

    def extract_video_ids_channel(self, channel_id: str) -> List[str]:
        artist = self.get_artist(channel_id)
        return self.extract_video_ids(artist["songs"]["browseId"])

    def download(self, v: List[str] = [], l: List[str] = [], c: List[str] = [], limit: int = 0, *args, **kwargs):
        """
        Main method of this class.
        """
        with ThreadPoolExecutor() as executor:
            futures: List[Future[List[str]]] = []
            for playlist_id in l:
                futures.append(executor.submit(
                    lambda x: self.extract_video_ids(x), playlist_id))
            for channel_id in c:
                futures.append(executor.submit(
                    lambda x: self.extract_video_ids_channel(x), channel_id))
            for future in futures:
                try:
                    res = future.result()
                    v.extend(res)
                except Exception as e:
                    print("skipping playlist, couldn't extract video ids: {} ({})".format(
                        e, e.__class__))

        v = list(set(v))
        print(f"starting to download {len(v)} tracks")
        downloaded_tracks = self.download_tracks(
            v, limit=limit, *args, **kwargs)
        print(f"downloaded {len(downloaded_tracks)} tracks")
        return downloaded_tracks


class CacheDownloader(Downloader):
    def __init__(self, download_dir: str, auth: str = None, debug: bool = False, cache: Cache = MemoryCache()):
        super().__init__(download_dir, auth, debug)
        self.cache = cache

    def download_tracks(self, video_ids: List[str], *args, **kwargs):
        uncached_video_ids = self.cache.filter_uncached(video_ids)
        print(f"download only uncached {len(uncached_video_ids)} tracks")

        downloaded_tracks = super().download_tracks(
            uncached_video_ids,
            after_download=lambda x: self.cache.add_items([x]), on_discarded=lambda x: self.cache.add_items(x),
            *args, **kwargs)
        self.cache.add_items(commit=True)
        return downloaded_tracks


class LibDownloader(CacheDownloader):
    def __init__(self, download_dir: str, auth: str = None, debug: bool = False, cache: Cache = MemoryCache()):
        super().__init__(download_dir, auth,  debug, cache=cache)

    def get_home_items(self, filter_titles: list) -> dict:
        """
        Returns home items in format of dict: { v: list, l: list, c: list }, that can be put into download function
        """
        home = self.get_home(limit=10)
        if filter_titles:
            home = list(filter(lambda x: x["title"] in filter_titles, home))

        home_items = [
            contents for home_item in home for contents in home_item["contents"]]

        res = dict(v=[], l=[], c=[])

        for home_item in home_items:
            if "videoId" in home_item:
                res['v'].append(home_item["videoId"])
            if "subscribers" in home_item and "browseId" in home_item:
                res['c'].append(home_item["browseId"])
            if "playlistId" in home_item:
                res["l"].append(home_item["playlistId"])

        return res

    personalised_home_titles = ["Listen again", "Mixed for you: moods",
                                "Quick picks", "Mixed for you", "Forgotten favorites"]

    def lib_update(self, limit: int = 0):
        print("Starting updating lib...")
        home_items = self.get_home_items(
            filter_titles=LibDownloader.personalised_home_titles)

        self.download(**home_items, limit=limit)
