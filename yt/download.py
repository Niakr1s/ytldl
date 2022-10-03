from concurrent.futures import ThreadPoolExecutor
import pathlib
from typing import Any, Dict, List
from yt_dlp import YoutubeDL
from yt.postprocessors import FilterPP, FilterPPException, LyricsPP, MetadataPP
from ytmusicapi import YTMusic


class Downloader(YTMusic):
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
            'default': '%(artist)s - %(title)s.%(ext)s',
        },
    }

    def __init__(self, download_dir: str, auth: str = None, user: str = None, requests_session=True, proxies: dict = None, language: str = 'en'):
        super().__init__(auth, user, requests_session, proxies, language)
        self.set_download_dir(download_dir)

    def set_download_dir(self, download_dir: str):
        pathlib.Path(download_dir).mkdir(parents=True, exist_ok=True)
        if 'paths' not in self._ydl_opts:
            self._ydl_opts['paths'] = {}
        self._ydl_opts['paths']['home'] = download_dir

    # returns download filepath
    def download_track(self, video_id: str):
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
        video_ids = set(video_ids)

        def download_track(video_id: str):
            self.download_track(video_id)

        with ThreadPoolExecutor() as executor:
            executor.map(download_track, video_ids)

    def extract_video_ids(self, playlist_id: str) -> List[str]:
        playlist = self.get_playlist(playlist_id)
        tracks: List[Any] = playlist['tracks']
        return map(lambda x: x['videoId'], tracks)

    # to use it, you should provide google auth headers
    # TODO: add explanation how to get them
    # returns download filepaths.
    def download_playlist(self, playlist_id: str):
        video_ids = self.extract_video_ids(playlist_id)
        self.download_tracks(video_ids)
