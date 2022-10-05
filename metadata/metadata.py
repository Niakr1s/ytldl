from email.mime import audio
import pathlib
import sys
from typing import Dict
import mutagen
from mutagen.mp4 import MP4, MP4FreeForm, AtomDataType, MP4Cover
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, USLT, TPE1, TIT2
from mutagen.oggvorbis import OggVorbis

# change it if you want debug script
debug = False


class UnknownFileType(Exception):
    pass


def write_metadata(filepath: str, metadata: Dict):
    file: mutagen.FileType = mutagen.File(filepath)
    if file.tags == None:
        file.add_tags()

    tag_keys: Dict[str, str] = {}

    if isinstance(file, MP4):
        file.tags["©ART"] = metadata["artist"]
        file.tags["©nam"] = metadata["title"]
        file.tags["©lyr"] = metadata["lyrics"]
        file.tags["----:com.apple.iTunes:WWW"] = MP4FreeForm(
            metadata["url"].encode("utf-8"), dataformat=AtomDataType.UTF8)

        if "thumbnail" in metadata:
            thumbnail = metadata["thumbnail"]
            file["covr"] = [MP4Cover(thumbnail)]
    else:
        raise UnknownFileType()

    file.save()


def printDebug(*args):
    if debug:
        print(args)
