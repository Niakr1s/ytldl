import pathlib
import shutil
import unittest

from ytmusicapi import YTMusic

from tests import consts
from ytldl.yt.download import Downloader, LibDownloader


class TestDownloader(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = pathlib.Path("tmp/test")
        if self.dir.exists():
            shutil.rmtree(self.dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def test_track_download_song_with_lyrics(self):
        d = Downloader(str(self.dir))
        d.download(videos=[consts.VIDEO_ID_SONG_WITH_LYRICS])
        self.assertTrue(len(list(self.dir.iterdir())) == 1)

    def test_track_download_song_without_lyrics(self):
        d = Downloader(str(self.dir))
        d.download(videos=[consts.VIDEO_ID_SONG_WITHOUT_LYRICS])
        self.assertTrue(len(list(self.dir.iterdir())) == 1)

    def test_track_download_video(self):
        d = Downloader(str(self.dir))
        d.download(videos=[consts.VIDEO_ID_VIDEO])
        self.assertTrue(len(list(self.dir.iterdir())) == 0)

    def tearDown(self):
        shutil.rmtree(self.dir)


class TestLibDownloader(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = pathlib.Path("tmp/test")
        if self.dir.exists():
            shutil.rmtree(self.dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    def test_get_home_items(self):
        d = LibDownloader(str(self.dir),
                          yt=YTMusic(auth=str(pathlib.Path.home() / ".ytldl" / "auth_headers.json")))
        home_items = d._get_home_items(LibDownloader._personalised_home_titles)
        print(home_items)

    def tearDown(self):
        shutil.rmtree(self.dir)


if __name__ == '__main__':
    unittest.main()
