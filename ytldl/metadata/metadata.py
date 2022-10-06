import mutagen
from mutagen.mp4 import MP4, MP4FreeForm, AtomDataType, MP4Cover


class UnknownFileType(Exception):
    pass


def write_metadata(filepath: str, metadata: dict):
    file: mutagen.FileType = mutagen.File(filepath)
    if file.tags == None:
        file.add_tags()

    if isinstance(file, MP4):
        if "artist" in metadata:
            file.tags["©ART"] = metadata["artist"]
        if "title" in metadata:
            file.tags["©nam"] = metadata["title"]
        if "lyrics" in metadata:
            file.tags["©lyr"] = metadata["lyrics"]
        if "url" in metadata:
            file.tags["----:com.apple.iTunes:WWW"] = MP4FreeForm(
                metadata["url"].encode("utf-8"), dataformat=AtomDataType.UTF8)
        if "thumbnail" in metadata:
            thumbnail = metadata["thumbnail"]
            file["covr"] = [MP4Cover(thumbnail)]
    else:
        raise UnknownFileType()

    file.save()
