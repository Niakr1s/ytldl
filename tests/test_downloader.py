import pathlib
import shutil
import unittest

from tests import consts
from ytldl.yt.download import Downloader
from ytldl.yt.postprocessors import FilterPPException


class TestDownloader(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = pathlib.Path("tmp/test")
        if self.dir.exists():
            shutil.rmtree(self.dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def test_track_download_song_with_lyrics(self):
        d = Downloader(str(self.dir))
        d.download_track(consts.VIDEO_ID_SONG_WITH_LYRICS)
        self.assertTrue(len(list(self.dir.iterdir())) == 1)

    def test_track_download_song_without_lyrics(self):
        d = Downloader(str(self.dir))
        d.download_track(consts.VIDEO_ID_SONG_WITHOUT_LYRICS)
        self.assertTrue(len(list(self.dir.iterdir())) == 1)

    def test_track_download_video(self):
        d = Downloader(str(self.dir))
        self.assertRaises(FilterPPException,
                          d.download_track, consts.VIDEO_ID_VIDEO)
        self.assertTrue(len(list(self.dir.iterdir())) == 0)

    def tearDown(self):
        shutil.rmtree(self.dir)


if __name__ == '__main__':
    unittest.main()
