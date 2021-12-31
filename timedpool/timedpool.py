"""A dict with a maximum size whose elements are deleted after a delay.

Adapted from https://stackoverflow.com/a/3927345/6571785
"""
import logging
import threading
from datetime import datetime, timedelta
from typing import Iterable, Tuple, TypeVar, Union

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")
Initial = Union[Iterable[Tuple[_KT, _VT]], dict[_KT, _VT]]


class TimedPool(dict[_KT, _VT]):
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

    Both `max_size` and `clean_t` must be greater or equal to 0, negative
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
        super().__init__()
        self.max_size = max_size if max_size >= 0 else 0
        self.ttl = ttl
        self.clean_t = clean_t if clean_t >= 0 else 0

        self._cv = threading.Condition()
        self._running = False
        self._thread = None
        self.start()

        if initial is not None:
            if isinstance(initial, dict):
                initial = initial.items()
            for k, v in initial:
                self.set(k, v)

    def _cleaner(self):
        """Removes expired items from this at regular intervals."""
        while self._running:
            with self._cv:
                now = datetime.now()
                deleting = [k for k, v in super().items()
                            if v['expireTime'] < now]
                for key in deleting:
                    super().__delitem__(key)
                if deleting:
                    logging.getLogger().debug("entries expired: %s", len(deleting))
                self._cv.wait(self.clean_t)

    def start(self):
        """Start the cleaning routine in a new thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._cleaner)
        self._thread.start()

    def stop(self):
        """Stops the cleaning routine and allows the thread to terminate."""
        if not self._running:
            return
        with self._cv:
            self._running = False
            self._cv.notify_all()
        self._thread.join()

    def set(self, key, val, ttl=None):
        """Adds a key-value pair to this.

        If `ttl` is not provided, the default duration is taken from the
        constructor.
        If this is full, this raises a `FullException`.
        """
        if ttl is None:
            ttl = self.ttl

        if len(self) >= self.max_size and not key in self:
            raise FullException()

        with self._cv:
            super().__setitem__(key, {
                'data': val,
                'expireTime': datetime.now() + ttl,
            })

    def get(self, key, default=None) -> _VT:
        if key in self:
            return super().get(key)['data']
        return default

    def clear(self) -> None:
        with self._cv:
            super().clear()

    def copy(self) -> dict[_KT, _VT]:
        # TODO: implement copy & test
        raise NotImplementedError()

    def pop(self, key, default=None) -> _VT:
        if key in self:
            val = self[key]
            del self[key]
            return val
        if default is not None:
            return default
        raise KeyError()

    def popitem(self) -> tuple[_KT, _VT]:
        with self._cv:
            item = super().popitem()
        return (item[0], item[1]['data'])

    def setdefault(self, key: _KT, default: _VT) -> _VT:
        # TODO: implement setdefault & test
        raise NotImplementedError()

    def update(self, **kwargs: _VT) -> None:
        # TODO: implement update & test
        raise NotImplementedError()

    def values(self):
        # TODO: implement values & test
        raise NotImplementedError()

    def items(self):
        # TODO: implement items & test
        raise NotImplementedError()

    def __getitem__(self, key: _KT) -> _VT:
        return self.get(key)

    def __setitem__(self, key: _KT, val: _VT) -> None:
        return self.set(key, val)

    def __delitem__(self, key) -> None:
        with self._cv:
            super().__delitem__(key)

    def __del__(self) -> None:
        self.stop()

    @classmethod
    def fromkeys(cls, iterable: Iterable[_KT], value: _VT = None) -> 'TimedPool[_KT, _VT | None]':
        pool = TimedPool()
        for i in iterable:
            pool[i] = value
        return pool


class FullException(Exception):
    """Exception signaling that the `TimedPool` is full."""
