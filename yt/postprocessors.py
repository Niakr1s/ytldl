import pathlib
import requests
from metadata.metadata import write_metadata
from ytmusicapi import YTMusic
from yt_dlp.postprocessor import PostProcessor
from typing import Any, Dict, List
from PIL import Image
from io import BytesIO


class LyricsPP(PostProcessor):
    """
    Gets lyrics and adds it to info
    """

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
        """
        Shouldn't throw invalid key exception
        """

        lyrics_browse_id = self.yt.get_watch_playlist(video_id).get("lyrics")
        if not lyrics_browse_id:
            return ""
        self.write_debug("Got lyrics browseId={}".format(lyrics_browse_id))

        lyrics = self.yt.get_lyrics(lyrics_browse_id).get("lyrics")
        if not lyrics:
            return ""

        return lyrics


class MetadataPP(PostProcessor):
    """
    Sets metadata to file:
    artist, title, lyrics, url
    """

    THUMBNAIL = "thumbnail"

    def __init__(self, downloader=None):
        super().__init__(downloader)
        self.metadata: dict = {}

    def run(self, info: Dict[str, Any]):
        self.metadata["artist"] = info["artist"]
        self.metadata["title"] = info["title"]
        self.metadata["url"] = info["webpage_url"]

        thumbnail = info[MetadataPP.THUMBNAIL]
        if thumbnail:
            self.metadata[MetadataPP.THUMBNAIL] = self.get_image_bytes(
                thumbnail)

        lyrics = info.get("lyrics")
        if lyrics:
            self.metadata["lyrics"] = lyrics

        self.filepath = info["filepath"]

        self.write_metadata()
        self.to_screen(
            "Wrote metadata to {}".format(self.filepath))

        return [], info

    def get_image_bytes(self, url: str, format: str = "JPEG") -> bytes:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img_jpg = BytesIO()
        img.save(img_jpg, format=format)
        return img_jpg.getvalue()

    def write_metadata(self):
        self.write_debug(
            "Starting to write metadata to {}".format(self.filepath))
        write_metadata(self.filepath, self.metadata)
