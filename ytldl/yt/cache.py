import pathlib
import sqlite3
from abc import ABCMeta, abstractmethod
from typing import Iterable


class Cache(metaclass=ABCMeta):
    @abstractmethod
    def filter_uncached(self, item: Iterable) -> set:
        """
        Should filter and return uncached items
        """
        pass

    @abstractmethod
    def add_items(self, items: Iterable):
        """
        Should cache items.
        """
        pass

    @abstractmethod
    def commit(self):
        """
        Should be called to commit, if cache uses batches.
        """
        pass

    @abstractmethod
    def close(self):
        """
        Should be called to close connections to db.
        """
        self.commit()


class MemoryCache(Cache):
    def __init__(self, init_items: Iterable = []):
        self.cache = set(init_items)

    def filter_uncached(self, items: Iterable) -> set:
        return set(items) - self.cache

    def add_items(self, items: Iterable):
        self.cache.update(items)

    def commit(self):
        super().commit()

    def close(self):
        super().close()


class SqliteCache(Cache):
    def __init__(self, path: str, batch_size: int = 0):
        """
        batch_size = 0 means, that add_items() will write items immediatly.
        """
        self.batch_size = batch_size
        self.batch = []
        self.path = pathlib.Path(path)
        path_existed = self.path.exists()

        self.con = sqlite3.connect(path)
        if not path_existed:
            self._create_v1()
        self._try_migrate()

        self.cur = self.con.cursor()

    def filter_uncached(self, items: Iterable) -> set:
        items = list(items)
        in_str = ', '.join(["?"] * len(items))
        exec = self.cur.execute(
            f'SELECT item FROM items WHERE item IN ({in_str});', items)
        cached = {item[0] for item in exec.fetchall()}
        uncached = set(items).difference(cached)
        return uncached

    def add_items(self, items: Iterable):
        self.batch.extend(items)

        exceeds_batch_size = self.batch_size != 0 and len(
            self.batch) >= self.batch_size

        if self.batch_size == 0 or exceeds_batch_size:
            self.commit()

    def commit(self):
        """
        adds items in batch and clears it
        """
        print(f"inserting {len(self.batch)} items into db")
        if len(self.batch) == 0:
            return

        self.cur.executemany('INSERT OR IGNORE INTO "items" ("item", "time") VALUES (?, CURRENT_TIMESTAMP);', [
            [item] for item in self.batch])
        self.con.commit()
        self.batch = []

    def close(self):
        super().close()
        self.con.close()

    def _create_v1(self):
        self.con.execute(
            'CREATE TABLE "items" ("item" varchar(50) UNIQUE NOT NULL);')
        self.con.commit()

    def _try_migrate(self):
        try:
            self.con.execute('ALTER TABLE "items" ADD COLUMN "time" timestamp DEFAULT NULL;')
        except sqlite3.OperationalError as e:
            is_duplicate = str(e).find("duplicate column") != -1
            if not is_duplicate:
                raise e
        finally:
            self.con.execute('UPDATE "items" SET "time" = CURRENT_TIMESTAMP;')
            self.con.commit()
