"""A dict with a maximum size whose elements are deleted after a delay.

Adapted from https://stackoverflow.com/a/3927345/6571785
"""
import asyncio
import logging
import threading
import time
from datetime import datetime, timedelta


class TimedPool(object):
    """A dict with a maximum size whose elements are deleted after a delay.

    This object can be used as a dictionary:
        p = TimedPool()
        p[key] = value
        if key in p:
            print(p[key])
        print(len(p))

    The difference with a normal dictionary is that this can contain a maximum
    number of objects, after which insertions will raise a `FullException`.
    Furthermore, each item is removed after a certain amount of time.
    Items are not removed immediately, but at fixed intervals.

    :ivar max_size: the maximum number of items in this
    :ivar lease_d: a duration after which an item can be removed from this dict
    :ivar cleaning_interval: seconds between runs of the cleaning routine
    """

    def __init__(self,
                 max_size: int = 10,
                 lease_d: timedelta = timedelta(hours=1),
                 cleaning_interval: int = 120):
        self.max_size = max_size
        self.lease_d = lease_d
        self.cleaning_interval = cleaning_interval

        self.cache = {}
        self.lock = threading.Lock()
        self.running = True
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever)
        self.thread.start()
        asyncio.run_coroutine_threadsafe(self.cleaner(), self.loop)

    async def cleaner(self):
        """Removes expired items from this at regular intervals."""
        while self.running:
            with self.lock:
                now = datetime.now()
                deleting = [k for k, v in self.cache.items()
                            if v["expireTime"] < now]
                for key in deleting:
                    del self.cache[key]
            if deleting:
                logging.getLogger().debug("entries expired: %s", len(deleting))
            await asyncio.sleep(self.cleaning_interval)

    def stop(self):
        """Stops the cleaning routine and allows the thread to terminate."""
        self.running = False
        time.sleep(1)  # otherwise when logging is active this raises NameError
        self.loop.call_soon_threadsafe(self.loop.stop)

    def __setitem__(self, key, val):
        return self.set(key, val)

    def __getitem__(self, key):
        return self.cache[key]["data"]

    def __delitem__(self, key):
        with self.lock:
            del self.cache[key]

    def __contains__(self, key):
        return key in self.cache

    def __len__(self):
        return len(self.cache)

    def set(self, key, val, lease_duration=None):
        """Adds a key-value pair to this.

        If lease_duration is not provided, the default duration is taken from
        the constructor.
        If this is full, this raises a `FullException`.
        """
        if lease_duration is None:
            lease_duration = self.lease_d

        if len(self.cache) >= self.max_size and not key in self.cache:
            raise FullException()

        with self.lock:
            self.cache[key] = {
                'data': val,
                'expireTime': datetime.now() + lease_duration,
            }


class FullException(Exception):
    """Exception signaling that the `TimedPool` is full."""
