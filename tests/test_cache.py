import os
import pathlib
import shutil
import unittest

from ytldl.yt.cache import Cache, MemoryCache, SqliteCache


class ITestCache:
    class TestCache(unittest.TestCase):
        def __init__(self, methodName: str = ...) -> None:
            super().__init__(methodName)
            self.cache: Cache

        init_cache = [str(i) for i in range(3)]
        test_sequence = [str(i + 1) for i in range(4)]
        want_sequence = {'3', '4'}

        def setUp(self) -> None:
            self.fill_cache()

        def fill_cache(self):
            self.cache.add_items(self.init_cache)

        def test_add_items(self):
            self.assertEqual(self.cache.filter_uncached(
                self.test_sequence), self.want_sequence)

        def tearDown(self) -> None:
            self.cache.commit()
            self.cache.close()


class TestMemoryCache(ITestCache.TestCache):
    def setUp(self) -> None:
        self.cache = MemoryCache()
        super().setUp()


class TestSqliteCache(ITestCache.TestCache):
    db_path = pathlib.Path() / "db" / "db.db"

    def setUp(self) -> None:
        shutil.rmtree(self.db_path.parent, ignore_errors=True)
        os.mkdir(self.db_path.parent)

        # setting batch_size 2 to test batch
        self.cache = SqliteCache(str(self.db_path), batch_size=2)
        super().setUp()

    def test_backup(self):
        SqliteCache(str(self.db_path), batch_size=2)
        self.assertEqual(3, len(os.listdir(self.db_path.parent)))

    def test_batch(self):
        self.assertEqual(self.cache.batch_size, 2)
        self.assertEqual(len(self.cache.batch), 0)
        self.cache.add_items({'10'})
        self.assertEqual(len(self.cache.batch), 1)
        self.cache.add_items({'11'})
        self.assertEqual(len(self.cache.batch), 0)

    def tearDown(self) -> None:
        super().tearDown()
        shutil.rmtree(self.db_path.parent, ignore_errors=True)

    def test_migrations(self):
        dbv1PathSrc = pathlib.Path("test_data/v1.db")
        dbv1Path = pathlib.Path("test_data/v1_test.db")
        shutil.copyfile(dbv1PathSrc, dbv1Path)

        SqliteCache(str(dbv1Path))
        # just checking, that second call doesn't raise exception
        SqliteCache(str(dbv1Path))

        dbv1Path.unlink()


if __name__ == '__main__':
    unittest.main()
