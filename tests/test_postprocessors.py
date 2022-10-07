import pathlib
import shutil
import unittest

from tests import consts
from ytldl.yt.postprocessors import FilterPP, FilterPPException, LyricsPP, MetadataPP


class TestLyricsPP(unittest.TestCase):
    def setUp(self) -> None:
        self.info = dict(id="changeme")
        self.lyrics_pp = LyricsPP()

    def test_with_lyrics(self):
        self.info["id"] = consts.VIDEO_ID_SONG_WITH_LYRICS
        _, info = self.lyrics_pp.run(self.info)
        self.assertIn("lyrics", info)
        self.assertTrue(info["lyrics"])

    def test_without_lyrics(self):
        self.info["id"] = consts.VIDEO_ID_SONG_WITHOUT_LYRICS
        _, info = self.lyrics_pp.run(self.info)
        self.assertIn("lyrics", info)
        self.assertFalse(info["lyrics"])


class TestMetadataPP(unittest.TestCase):
    input_filepath = pathlib.Path("test_data/test_audio_no_tags.m4a")
    filepath = pathlib.Path("test_data/test_audio_no_tags_copy.m4a")

    def setUp(self) -> None:
        self.metadata_pp = MetadataPP()
        self.metadata = dict(artist="artist", title="title", webpage_url="url",
                             thumbnail="https://i.ytimg.com/vi_webp/pm9JyMiAU6A/maxresdefault.webp",
                             filepath=str(self.filepath))
        shutil.copyfile(self.input_filepath, self.filepath)

    def test_correct_metadata(self):
        self.metadata_pp.run(self.metadata)

    def test_correct_metadata_filepath_only(self):
        self.metadata = dict(filepath=str(self.filepath))
        self.metadata_pp.run(self.metadata)

    def test_empty_metadata(self):
        self.metadata.clear()
        self.assertRaises(Exception, self.metadata_pp.run, self.metadata)

    def test_metadata_without_filepath(self):
        self.metadata.pop("filepath")
        self.assertRaises(Exception, self.metadata_pp.run, self.metadata)

    def tearDown(self) -> None:
        self.filepath.unlink()


class TestFilterPP(unittest.TestCase):
    def setUp(self) -> None:
        self.filter_pp = FilterPP()

    def test_correct_info(self):
        info = dict(artist="artist", title="title")
        self.filter_pp.run(info)

    def test_no_artist_info(self):
        info = dict(title="title")
        self.assertRaises(FilterPPException, self.filter_pp.run, info)


if __name__ == '__main__':
    unittest.main()
