import pathlib
import shutil
import unittest
from mutagen.mp4 import MP4, MP4FreeForm, AtomDataType, MP4Cover
from PIL import Image

from ytldl.metadata.metadata import write_metadata


class TestWriteMetadata(unittest.TestCase):
    input_filepath = pathlib.Path("test_data/test_audio_no_tags.m4a")
    filepath = pathlib.Path("test_data/test_audio_no_tags_copy.m4a")

    metadata_to_write = dict(
        artist="artist", title="title", lyrics="lyrics", url="url",
        thumbnail=Image.open("test_data/img.jpg").tobytes())

    def setUp(self) -> None:
        shutil.copyfile(self.input_filepath, self.filepath)

    def test_write_metadata(self):
        write_metadata(str(self.filepath), self.metadata_to_write)

        audio = MP4(str(self.filepath))
        self.assertIsNotNone(audio.tags)
        keys = set(audio.tags.keys())
        want = {"©ART", "©nam", "©lyr",
                "----:com.apple.iTunes:WWW", "covr"}
        self.assertTrue(want.issubset(keys))

    def test_write_empty_metadata(self):
        write_metadata(str(self.filepath), {})
        audio = MP4(str(self.filepath))
        self.assertIsNotNone(audio.tags)
        keys = set(audio.tags.keys())
        not_want = {"©ART", "©nam", "©lyr",
                    "----:com.apple.iTunes:WWW", "covr"}
        self.assertTrue(len(not_want.intersection(keys)) == 0)

    def tearDown(self) -> None:
        self.filepath.unlink()


if __name__ == '__main__':
    unittest.main()
