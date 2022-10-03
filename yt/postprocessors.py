import pathlib
from metadata.metadata import write_metadata
from ytmusicapi import YTMusic
from yt_dlp.postprocessor import PostProcessor
from typing import Any, Dict, List


class LyricsPP(PostProcessor):
    """
    Gets lyrics and adds it to info
    """

    yt: YTMusic

    def __init__(self, downloader=None):
        super().__init__(downloader)
        self.yt = YTMusic()

    def run(self, info):
        video_id = info["id"]
        lyrics = ""
        try:
            lyrics = self.get_lyrics(video_id)
        except:
            pass
        self.to_screen("Got lyrics with len={}".format(len(lyrics)))
        info["lyrics"] = lyrics
        return [], info

    def get_lyrics(self, video_id: str) -> str:
        watch_playlist = self.yt.get_watch_playlist(video_id)
        lyrics_browse_id = watch_playlist["lyrics"]
        self.write_debug("Got lyrics browseId={}".format(lyrics_browse_id))

        lyrics: str = self.yt.get_lyrics(lyrics_browse_id)["lyrics"]
        return lyrics


class MetadataPP(PostProcessor):
    """
    Sets metadata to file:
    artist, title, lyrics, url
    """

    # metadata, that will be written
    metadata: Dict[str, str] = {}

    # filepath, metadata will be written to
    filepath: str

    def run(self, info: Dict[str, Any]):
        self.metadata["artist"] = info["artist"]
        self.metadata["title"] = info["title"]
        self.metadata["url"] = info["webpage_url"]

        lyrics = info.get("lyrics")
        if lyrics:
            self.metadata["lyrics"] = lyrics

        self.filepath = info["filepath"]

        self.write_metadata()
        self.to_screen(
            "Wrote metadata to {}".format(self.filepath))

        return [], info

    def write_metadata(self):
        self.write_debug(
            "Starting to write metadata to {}".format(self.filepath))
        write_metadata(self.filepath, self.metadata)


class InfoExtractorPP(PostProcessor):
    """
    Extracts result info
    """

    info: Dict[str, Any]

    def run(self, info: Dict[str, Any]):
        self.info = info
        return super().run(info)


def is_song(info: Dict[str, Any]) -> bool:
    return all(k in info for k in ["artist", "title"])


class FilterPPException(Exception):
    pass


class FilterPP(PostProcessor):
    """
    Filters unwanted songs.
    """

    info: Dict[str, Any]

    def run(self, info: Dict[str, Any]):
        if not is_song(info):
            raise FilterPPException()
        return [], info
