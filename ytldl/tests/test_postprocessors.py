import unittest
from ytldl.yt.postprocessors import LyricsPP


class TestLyricsPP(unittest.TestCase):
    VIDEO_ID_WITH_LYRICS = "pm9JyMiAU6A"
    VIDEO_ID_WITHOUT_LYRICS = "6qTyEOAWAOQ"

    def setUp(self) -> None:
        self.info = dict(id="changeme")
        self.lyrics_pp = LyricsPP()

    def test_with_lyrics(self):
        self.info["id"] = self.VIDEO_ID_WITH_LYRICS
        _, info = self.lyrics_pp.run(self.info)
        self.assertIn("lyrics", info)
        self.assertTrue(info["lyrics"])

    def test_without_lyrics(self):
        self.info["id"] = self.VIDEO_ID_WITHOUT_LYRICS
        _, info = self.lyrics_pp.run(self.info)
        self.assertIn("lyrics", info)
        self.assertFalse(info["lyrics"])


if __name__ == '__main__':
    unittest.main()
