from abc import ABCMeta, abstractmethod
import sqlite3


class Cache(metaclass=ABCMeta):
    @abstractmethod
    def filter_uncached(self, item: list) -> list:
        """
        Should filter and return uncached items
        """
        pass

    @abstractmethod
    def add_items(self, items: list):
        """
        Should cache items.
        """
        pass

    @abstractmethod
    def commit(self):
        """
        Should be called to finalize cache (write to disk etc).
        """
        pass


class MemoryCache(Cache):
    def __init__(self, init_items: list = []):
        self.cache = set(init_items)

    def filter_uncached(self, items: list) -> list:
        return list(self.cache.intersection(items))

    def add_items(self, items: list):
        self.cache.update(items)

    def commit(self):
        pass


class SqliteCache(Cache):
    def __init__(self, path: str, batch_size: int = 0):
        """
        batch_size = 0 means, that add_items() will write items immediatly.
        """
        self.batch_size = batch_size
        self.batch = []

        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()

    def filter_uncached(self, items: list) -> list:
        in_str = ', '.join(["?"]*len(items))
        exec = self.cur.execute(
            f'SELECT item FROM items WHERE item IN ({in_str});', items)
        cached = set([item[0] for item in exec.fetchall()])
        uncached = set(items).difference(cached)
        return uncached

    def _commit(self):
        """
        adds items in batch and clears it
        """
        print(f"inserting {len(self.batch)} items into db")
        self.cur.executemany('INSERT OR IGNORE INTO "items" ("item") VALUES (?);', [
            [item] for item in self.batch])
        self.con.commit()
        self.batch = []

    def add_items(self, items: list):
        self.batch.extend(items)

        exceeds_batch_size = self.batch_size != 0 and len(
            self.batch) >= self.batch_size

        if self.batch_size == 0 or exceeds_batch_size:
            self._commit()

    def commit(self):
        self._commit()

    def create(path: str):
        con = sqlite3.connect(path)
        con.execute(
            "CREATE TABLE items(item varchar(50) UNIQUE NOT NULL);")


if __name__ == "__main__":
    # some tests for SqliteCache
    import pathlib

    db = pathlib.Path("d:/Projects/ytldl/tmp/.ytldl/ytldl.db")
    db.parent.mkdir(exist_ok=True, parents=True)
    try:
        SqliteCache.create(db)
    except Exception:
        pass

    cache = SqliteCache(str(db))
    cache.add_items([str(i) for i in range(10)])
    uncached = cache.filter_uncached([str(i+5) for i in range(10)])
    print(uncached)
