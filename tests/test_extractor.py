import unittest

from ytmusicapi import YTMusic

from ytldl.yt.extractor import Extractor


class TestExtractor(unittest.TestCase):
    VALID_CHANNEL = "UCsXkTJM-ydmIkR5CuEWEloA"
    INVALID_CHANNEL = "fasdfvafq23f32"

    VALID_PLAYLIST = "RDCLAK5uy_n-3mnbQ8mP-0iKIBOvN_ng8VGu9QQ73ek"
    INVALID_PLAYLIST = "fasdf32f23fafewfaw"

    def setUp(self) -> None:
        self.extractor = Extractor(YTMusic())

    def test_extract_empty(self):
        self.assertTrue(sum(1 for i in self.extractor.extract()) == 0)

    def test_extract_videos(self):
        def data():
            return (str(i) for i in range(10))

        self.assertEqual(set(self.extractor.extract(videos=data())), set(data()))

    def test_extract_valid_channel(self):
        self.assertTrue(sum(1 for i in self.extractor.extract(
            channels=[self.VALID_CHANNEL]
        )) > 0)

    def test_extract_valid_playlist(self):
        self.assertTrue(sum(1 for i in self.extractor.extract(
            playlists=[self.VALID_PLAYLIST]
        )) > 0)

    def test_extract_invalid_channel(self):
        self.assertTrue(sum(1 for i in self.extractor.extract(
            channels=[self.INVALID_CHANNEL]
        )) == 0)

    def test_extract_invalid_playlist(self):
        self.assertTrue(sum(1 for i in self.extractor.extract(
            playlists=[self.INVALID_PLAYLIST]
        )) == 0)

    def test_extract_limit(self):
        self.assertTrue(sum(1 for i in self.extractor.extract(
            playlists=[self.VALID_PLAYLIST],
            channels=[self.VALID_CHANNEL],
            limit=0,
        )) == 0)


if __name__ == '__main__':
    unittest.main()
