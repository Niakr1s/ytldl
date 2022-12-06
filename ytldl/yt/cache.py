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
    def add_discarded_items(self, items: Iterable):
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

    def add_discarded_items(self, items: Iterable):
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

        # batch holds: (videoid: str, dodwnloaded: bool)
        self.batch = []

        self.path = pathlib.Path(path)
        path_existed = self.path.exists()

        self.con = sqlite3.connect(path)
        if not path_existed:
            self._create_v1()
        self._try_migrate()

        self.cur = self.con.cursor()

    def fix_downloaded_column(self, downloaded_items: list[str]):
        """
        Provided with list of downloaded items (e.g. videoId strings),
        it fixes downloaded column for all items.
        """
        self.con.execute('update items set downloaded = false;')
        self.con.executemany(
            'update items set downloaded = true where item = ?;',
            [[item] for item in downloaded_items])
        self.con.commit()

    def filter_uncached(self, items: Iterable) -> set:
        items = list(items)
        in_str = ', '.join(["?"] * len(items))
        exec = self.cur.execute(
            f'SELECT item FROM items WHERE item IN ({in_str});', items)
        cached = {item[0] for item in exec.fetchall()}
        uncached = set(items).difference(cached)
        return uncached

    def add_items(self, items: Iterable):
        # downloaded = False
        self.batch.extend([(item, True) for item in items])
        self._try_batch_commit()

    def add_discarded_items(self, items: Iterable):
        # downloaded = True
        self.batch.extend([(item, False) for item in items])
        self._try_batch_commit()

    def _try_batch_commit(self):
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

        self.cur.executemany(
            'INSERT OR IGNORE INTO "items" ("item", "time", "downloaded") VALUES (?, CURRENT_TIMESTAMP, ?);',
            [item for item in self.batch])
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
            if not self._is_duplicate_error(e):
                raise e
        finally:
            self.con.execute('UPDATE "items" SET "time" = CURRENT_TIMESTAMP where "time" IS NULL OR "time" = "";')
            self.con.commit()

        try:
            self.con.execute('ALTER TABLE "items" ADD COLUMN "downloaded" bool DEFAULT false;')
        except sqlite3.OperationalError as e:
            if not self._is_duplicate_error(e):
                raise e
        finally:
            self.con.commit()

    @staticmethod
    def _is_duplicate_error(e: sqlite3.DatabaseError):
        return str(e).find("duplicate column") != -1
