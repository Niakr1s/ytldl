from abc import ABCMeta, abstractmethod


class Cache(metaclass=ABCMeta):
    @abstractmethod
    def is_in_cache(self, item) -> bool:
        pass


class MemoryCache(Cache):
    def __init__(self, init_items: list = []):
        self.cache = set(init_items)

    def is_in_cache(self, item) -> bool:
        return item in self.cache
