from concurrent.futures import Future, ThreadPoolExecutor
from functools import partial
import pathlib
from typing import Any, Dict, List
from yt_dlp import YoutubeDL
from util.exxception import try_or
from yt.postprocessors import FilterPP, FilterPPException, LyricsPP, MetadataPP
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

    def __init__(self, download_dir: str, auth: str = None, user: str = None, requests_session=True, proxies: dict = None, language: str = 'en',
                 debug: bool = False):
        super().__init__(auth, user, requests_session, proxies, language)
        self.debug = debug
        self.set_download_dir(download_dir)

    def set_download_dir(self, download_dir: str):
        pathlib.Path(download_dir).mkdir(parents=True, exist_ok=True)
        if 'paths' not in self._ydl_opts:
            self._ydl_opts['paths'] = {}
        self._ydl_opts['paths']['home'] = download_dir

    # returns download filepath
    def download_track(self, video_id: str):
        if self.debug:
            return

        url = "https://youtube.com/watch?v={}".format(video_id)

        try:
            with YoutubeDL(self._ydl_opts) as ydl:
                ydl.add_post_processor(FilterPP(), when='pre_process')
                ydl.add_post_processor(LyricsPP(), when='post_process')
                ydl.add_post_processor(MetadataPP(), when='post_process')

                ydl.download([url])

        except FilterPPException:
            print("skipping due to FilterPP")
        except Exception as e:
            print("couldn't download {}: {}".format(video_id, e))

    def download_tracks(self, video_ids: List[str]):
        """
        Downloads several tracks, based on their video_ids in thread pool.
        Uses set() to not to allow video_ids doublicates.
        """
        video_ids = set(video_ids)

        def download_track(video_id: str):
            self.download_track(video_id)

        with ThreadPoolExecutor() as executor:
            futures: List[Future] = []
            for video_id in video_ids:
                futures.append(executor.submit(download_track, video_id))
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    print("couldn't download video: {}".format(e))

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

    # to use it, you should provide google auth headers
    # TODO: add explanation how to get them
    # returns download filepaths.
    def download_playlist(self, playlist_id: str):
        video_ids = self.extract_video_ids(playlist_id)
        self.download_tracks(video_ids)

    def download(self, v: List[str] = [], l: List[str] = [], c: List[str] = []):
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

        v = set(v)
        print("starting to download {} tracks".format(len(v)))
        self.download_tracks(v)
