"""A dict with a maximum size whose elements are deleted after a delay.

Adapted from https://stackoverflow.com/a/3927345/6571785
"""
import asyncio
from collections import UserDict
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Iterable, Tuple, TypeVar, Union

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
Initial = Union[Iterable[tuple[_KT, _VT]], dict[_KT, _VT]]


class TimedPool(dict):
    """A dict with a maximum size whose elements are deleted after a delay.

    This object can be used as a dictionary:
    ```
    p = TimedPool()
    p[key] = value
    if key in p:
        print(p[key])
    print(len(p))
    del p[key]
    ```

    The difference with a normal dictionary is that this can contain a maximum
    number of objects, after which insertions will raise a `FullException`.
    Furthermore, each item can be removed after a certain amount of time (ttl).
    Items are not removed immediately, but at fixed intervals.

    Using `p[key] = value` will apply the default ttl; instead,
    `p.set(ket, value, ttl)` allows to set a specific ttl.

    The `stop()` method can be used to stop the cleaning routine.

    Both `max_size` and `clean_t` must be greather or equal to 0, negative
    values are rounded to 0.

    The `initial` parameter can be an iterable of tuples that is used to
    populate the pool with some elements.
    It is equivalent to adding each key-value tuple to the pool in the order
    provided by the iterable. If `initial` is a dictionary, its elements will
    be added in the order provided by the dictionary `items()` method.

    :ivar max_size: the maximum number of items in this
    :ivar ttl: a duration after which an item can be removed from this dict
    :ivar clean_t: seconds between runs of the cleaning routine
    :param initial: the initial values of this dict
    """

    def __init__(self,
                 max_size: int = 10,
                 ttl: timedelta = timedelta(hours=1),
                 clean_t: int = 120,
                 initial: Initial = None):
        self.max_size = max_size if max_size >= 0 else 0
        self.ttl = ttl
        self.clean_t = clean_t if clean_t >= 0 else 0

        self._cache = {}
        self._lock = threading.Lock()
        self._running = True
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever)
        self._thread.start()
        asyncio.run_coroutine_threadsafe(self._cleaner(), self._loop)

        if initial is not None:
            if isinstance(initial, dict):
                initial = initial.items()
            for k, v in initial:
                try:
                    self.set(k, v)
                except FullException:
                    pass

    async def _cleaner(self):
        """Removes expired items from this at regular intervals."""
        while self._running:
            with self._lock:
                now = datetime.now()
                deleting = [k for k, v in self._cache.items()
                            if v["expireTime"] < now]
                for key in deleting:
                    del self._cache[key]
            if deleting:
                logging.getLogger().debug("entries expired: %s", len(deleting))
            await asyncio.sleep(self.clean_t)

    def stop(self):
        """Stops the cleaning routine and allows the thread to terminate."""
        self._running = False
        time.sleep(1)  # otherwise when logging is active this raises NameError
        self._loop.call_soon_threadsafe(self._loop.stop)

    def __setitem__(self, key, val):
        return self.set(key, val)

    def __getitem__(self, key):
        return self._cache[key]["data"]

    def __delitem__(self, key):
        with self._lock:
            del self._cache[key]

    def __contains__(self, key):
        return key in self._cache

    def __len__(self):
        return len(self._cache)

    def set(self, key, val, ttl=None):
        """Adds a key-value pair to this.

        If `ttl` is not provided, the default duration is taken from the
        constructor.
        If this is full, this raises a `FullException`.
        """
        if ttl is None:
            ttl = self.ttl

        if len(self._cache) >= self.max_size and not key in self._cache:
            raise FullException()

        with self._lock:
            self._cache[key] = {
                'data': val,
                'expireTime': datetime.now() + ttl,
            }

    def clear(self):
        self._cache.clear()


class FullException(Exception):
    """Exception signaling that the `TimedPool` is full."""
