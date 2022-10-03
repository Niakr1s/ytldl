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


# ----------- CLEAN ------------
def cleanMetadata(musicFilePath: str):
    printDebug("start cleanMetadata to ", musicFilePath)
    ext = pathlib.Path(musicFilePath).suffix
    if ext == ".mp3":
        cleanMetadataMp3(musicFilePath)
    elif ext == ".ogg":
        cleanMetadataOgg(musicFilePath)
    else:
        raise Exception("wrong extension, want .mp3 or .ogg")
    printDebug("end cleanMetadata to ", musicFilePath)


def cleanMetadataMp3(musicFilePath: str):
    printDebug("start cleanMetadataMp3 to ", musicFilePath)
    audio = MP3(musicFilePath)
    # audio = ID3(musicFilePath)
    audio.tags = None
    audio.add_tags()
    # audio.clear()
    audio.save()


def cleanMetadataOgg(musicFilePath: str):
    printDebug("start cleanMetadataOgg to ", musicFilePath)
    audio = OggVorbis(musicFilePath)
    audio.clear()
    audio.save()


# ----------- LYRICS ------------
def writeLyrics(musicFilePath: str, contents: str):
    printDebug("start writeLyrics to ", musicFilePath)
    ext = pathlib.Path(musicFilePath).suffix
    if ext == ".mp3":
        writeLyricsMp3(musicFilePath, contents)
    elif ext == ".ogg":
        writeLyricsOgg(musicFilePath, contents)
    else:
        raise Exception("wrong extension, want .mp3 or .ogg")
    printDebug("end writeLyrics to ", musicFilePath)


def writeLyricsMp3(musicFilePath: str, contents: str):
    printDebug("start writeLyricsMp3 to ", musicFilePath)
    # audio = ID3(musicFilePath)
    # audio.add(USLT(lang='   ', desc='', text=contents))
    audio = MP3(musicFilePath)
    if audio.tags is None:
        audio.add_tags()
    audio = ID3(musicFilePath)
    audio.add(USLT(lang='   ', desc='', text=contents))
    audio.save()


def writeLyricsOgg(musicFilePath: str, contents: str):
    printDebug("start writeLyricsOgg to ", musicFilePath)
    audio = OggVorbis(musicFilePath)
    audio['lyrics'] = contents
    audio.save()


# ----------- ARTIST ------------
def writeArtist(musicFilePath: str, contents: str):
    printDebug("start writeArtist to ", musicFilePath)
    ext = pathlib.Path(musicFilePath).suffix
    if ext == ".mp3":
        writeArtistMp3(musicFilePath, contents)
    elif ext == ".ogg":
        writeArtistOgg(musicFilePath, contents)
    else:
        raise Exception("wrong extension, want .mp3 or .ogg")
    printDebug("end writeArtist to ", musicFilePath)


def writeArtistMp3(musicFilePath: str, contents: str):
    printDebug("start writeArtistMp3 to ", musicFilePath)
    # audio = ID3(musicFilePath)
    # audio.add(TPE1(text=contents))
    audio = MP3(musicFilePath)
    if audio.tags is None:
        audio.add_tags()
    audio = ID3(musicFilePath)
    audio.add(TPE1(text=contents))
    audio.save()


def writeArtistOgg(musicFilePath: str, contents: str):
    printDebug("start writeArtistOgg to ", musicFilePath)
    audio = OggVorbis(musicFilePath)
    audio['artist'] = contents
    audio.save()


# ----------- TITLE ------------
def writeTitle(musicFilePath: str, contents: str):
    printDebug("start writeTitle to ", musicFilePath)
    ext = pathlib.Path(musicFilePath).suffix
    if ext == ".mp3":
        writeTitleMp3(musicFilePath, contents)
    elif ext == ".ogg":
        writeTitleOgg(musicFilePath, contents)
    else:
        raise Exception("wrong extension, want .mp3 or .ogg")
    printDebug("end writeTitle to ", musicFilePath)


def writeTitleMp3(musicFilePath: str, contents: str):
    printDebug("start writeTitleMp3 to ", musicFilePath)
    # audio = ID3(musicFilePath)
    # audio.add(TIT2(text=contents))
    audio = MP3(musicFilePath)
    if audio.tags is None:
        audio.add_tags()
    audio = ID3(musicFilePath)
    audio.add(TIT2(text=contents))
    audio.save()


def writeTitleOgg(musicFilePath: str, contents: str):
    printDebug("start writeTitleOgg to ", musicFilePath)
    audio = OggVorbis(musicFilePath)
    audio['title'] = contents
    audio.save()

# ----------------------------------


def run():
    usage = """Usage:
lyrics [filepath] [contents] - Writes lyrics to audiofile
artist [filepath] [contents] - Writes artist to audiofile
title [filepath] [contents] - Writes title to audiofile
clean [filepath] - Erases metadata from audiofile
"""

    # 0             1      2        3
    # "metadata.py" lyrics file.mp3 "some cool lyrics"
    args = sys.argv

    # 3 is minimum arguments
    if len(args) < 3:
        printDebug(usage)
        raise Exception("not enough arguments")

    action = sys.argv[1]
    filePath = sys.argv[2]

    if action == "clean":
        cleanMetadata(filePath)
        return

    if len(args) < 4:
        printDebug(usage)
        raise Exception("not enough arguments")
    contents = sys.argv[3]

    if action == "lyrics":
        writeLyrics(filePath, contents)
    elif action == "artist":
        writeArtist(filePath, contents)
    elif action == "title":
        writeTitle(filePath, contents)
    else:
        raise Exception("wrong action ", action)


if __name__ == "__main__":
    run()
