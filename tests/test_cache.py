import pathlib
import unittest

from ytldl.yt.cache import Cache, MemoryCache, SqliteCache


class ITestCache:
    class TestCache(unittest.TestCase):
        def __init__(self, methodName: str = ...) -> None:
            super().__init__(methodName)
            self.cache: Cache

        init_cache = [str(i) for i in range(3)]
        test_sequence = [str(i+1) for i in range(4)]
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
    db_path = pathlib.Path() / "db.db"

    def setUp(self) -> None:
        self.db_path.unlink(missing_ok=True)
        SqliteCache.create(str(self.db_path))

        # setting batch_size 2 to test batch
        self.cache = SqliteCache(str(self.db_path), batch_size=2)
        super().setUp()

    def test_batch(self):
        self.assertEqual(self.cache.batch_size, 2)
        self.assertEqual(len(self.cache.batch), 0)
        self.cache.add_items({'10'})
        self.assertEqual(len(self.cache.batch), 1)
        self.cache.add_items({'11'})
        self.assertEqual(len(self.cache.batch), 0)

    def tearDown(self) -> None:
        super().tearDown()
        self.db_path.unlink()


if __name__ == '__main__':
    unittest.main()
