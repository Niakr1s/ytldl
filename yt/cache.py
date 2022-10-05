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
        pass


class MemoryCache(Cache):
    def __init__(self, init_items: list = []):
        self.cache = set(init_items)

    def filter_uncached(self, items: list) -> list:
        return list(self.cache.intersection(items))

    def add_items(self, items: list):
        self.cache.update(items)


class SqliteCache(Cache):
    def __init__(self, path: str):
        self.con = sqlite3.connect(path)
        self.cur = self.con.cursor()

    def filter_uncached(self, items: list) -> list:
        in_str = ', '.join(["?"]*len(items))
        exec = self.cur.execute(
            f'SELECT item FROM items WHERE item IN ({in_str});', items)
        cached = set([item[0] for item in exec.fetchall()])
        uncached = set(items).difference(cached)
        return uncached

    def add_items(self, items: list):
        self.cur.executemany('INSERT OR IGNORE INTO "items" ("item") VALUES (?);', [
            [item] for item in items])

        self.con.commit()

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
