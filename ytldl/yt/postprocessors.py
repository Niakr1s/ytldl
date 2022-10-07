from io import BytesIO
from typing import Any, Dict

import requests
from PIL import Image
from yt_dlp.postprocessor import PostProcessor
from ytmusicapi import YTMusic

from ytldl.metadata.metadata import write_metadata


class LyricsPP(PostProcessor):
    """
    Gets lyrics and adds it to info
    """

    def __init__(self, downloader=None):
        super().__init__(downloader)
        self.yt = YTMusic()

    def run(self, info):
        video_id = info["id"]
        lyrics = self.get_lyrics(video_id) or ""
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

    def run(self, info: Dict[str, Any]):
        metadata = dict(artist=info.get("artist", ""),
                        title=info.get("title", ""),
                        url=info.get("webpage_url", ""),
                        lyrics=info.get("lyrics", ""))

        thumbnail = info.get(MetadataPP.THUMBNAIL)
        if thumbnail:
            metadata[MetadataPP.THUMBNAIL] = self.get_image_bytes(
                thumbnail)

        filepath = info["filepath"]
        self.write_debug(
            "Starting to write metadata to {}".format(filepath))
        write_metadata(filepath, metadata)
        self.to_screen(
            "Wrote metadata to {}".format(filepath))

        return [], info

    def get_image_bytes(self, url: str, format: str = "JPEG") -> bytes:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img_jpg = BytesIO()
        img.save(img_jpg, format=format)
        return img_jpg.getvalue()


def is_song(info: Dict[str, Any]) -> bool:
    return all(k in info for k in ["artist", "title"])


class FilterPPException(Exception):
    pass


class FilterPP(PostProcessor):
    """
    Filters unwanted songs.
    """

    def run(self, info: Dict[str, Any]):
        if not is_song(info):
            raise FilterPPException()
        return [], info
