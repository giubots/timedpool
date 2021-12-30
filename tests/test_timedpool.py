# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=import-error
from collections import UserDict
from unittest import TestCase

from src.timedpool import TimedPool, FullException


class TestTimedPool(TestCase):
    def setUp(self) -> None:
        obj = object()
        self.el = {
            123: 'abc',
            'abc': "def",
            obj: True,
            'none': None,
            'list': [1, 'two']
        }

    def test_setitem_getitem(self):
        p = TimedPool()
        for k, v in self.el.items():
            p[k] = v

        for k, v in self.el.items():
            self.assertEqual(v, p[k])
        p.stop()

    def test_set_getitem(self):
        p = TimedPool()
        for k, v in self.el.items():
            p.set(k, v)

        for k, v in self.el.items():
            self.assertEqual(v, p[k])
        p.stop()

    def test_init_size(self):
        for size in range(len(self.el.items())):
            p = TimedPool(max_size=size)
            items = list(self.el.items())

            for i in range(size):
                p[items[i][0]] = items[i][1]

            for i in range(size, len(items)):
                with self.assertRaises(FullException):
                    p[items[i][0]] = items[i][1]

            for i in range(size):
                self.assertEqual(items[i][1], p[items[i][0]])
            p.stop()

    def test_init_size_invalid(self):
        p = TimedPool(max_size=-1)
        self.assertEqual(p.max_size, 0)
        p.stop()

    def test_init_clean_invalid(self):
        p = TimedPool(clean_t=-1)
        self.assertEqual(p.clean_t, 0)
        p.stop()


class TestTimedPoolCompat(TestCase):
    def setUp(self) -> None:
        obj = object()
        self.el = {
            123: 'abc',
            'abc': "def",
            obj: True,
            'none': None,
            'list': [1, 'two']
        }
        self.p = TimedPool(initial=self.el)
    
    def tearDown(self) -> None:
        self.p.stop()
        return super().tearDown()

    def test_clear(self):
        self.p.clear()
        self.assertEqual(len(self.p), 0)

    def test_is_dict(self):
        self.assertIsInstance(self.p, dict)