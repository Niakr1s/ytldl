from asyncio import Future
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

from ytmusicapi import YTMusic


class Extractor:
    def __init__(self, yt: YTMusic):
        self.yt = yt

    def extract(self,
                videos: Iterable[str] = None,
                playlists: Iterable[str] = None, channels: Iterable[str] = None,
                limit: int = 50) -> Iterable[str]:
        """
        Extracts videoIds from playlists and channels.
        You can pass list of videos to return them with result.
        Limit is used to limit track cound from EACH channel or playlist.
        Returns iterable of videoIds.
        """

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures: list[Future[Iterable[str]]] = []
            for playlist in (playlists or ()):
                futures.append(executor.submit(
                    self._extract_video_ids_from_playlist, playlist, limit=limit))
            for channel in (channels or ()):
                futures.append(executor.submit(
                    self.extract_video_ids_from_channel, channel, limit=limit))
            video_ids: list[str] = list(videos or ())
            for future in as_completed(futures):
                try:
                    video_ids += future.result()
                except Exception as e:
                    print(f"skipping playlist, couldn't extract video ids: {e}")
            print(f"[Extractor] Extracted {len(video_ids)} videos")
            return (video_id for video_id in video_ids)

    def _extract_video_ids_from_playlist(self, playlist: str, /, limit: int = 50) -> Iterable[str]:
        """
        Extracts videoIds from playlist.
        Returns iterable of videoIds.
        """

        try:
            contents = self.yt.get_playlist(playlistId=playlist, limit=limit)
        except Exception:
            try:
                contents = self.yt.get_watch_playlist(playlistId=contents, limit=limit)
            except Exception as e:
                raise Exception(f"couldn't get songs from {playlist}")
        tracks: list = contents['tracks']
        tracks = tracks[:min(limit, len(tracks))]

        return (track['videoId'] for track in tracks)

    def extract_video_ids_from_channel(self, channel: str, /, limit: int = 50) -> Iterable[str]:
        """
        Extracts videoIds from channel.
        Returns iterable of videoIds.
        """
        artist = self.yt.get_artist(channel)
        return self._extract_video_ids_from_playlist(artist["songs"]["browseId"], limit=limit)
