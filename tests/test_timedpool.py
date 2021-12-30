# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=invalid-name
# pylint: disable=import-error
import time
from datetime import timedelta
from unittest import TestCase

from src.timedpool import FullException, TimedPool


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

    def test_deletion(self):
        p = TimedPool(ttl=timedelta(seconds=1), clean_t=1)
        p['key'] = 'value'
        self.assertEqual(p['key'], 'value')

        time.sleep(3)

        self.assertFalse('key' in p)
        p.stop()


class TestTimedPoolCompat(TestCase):
    def setUp(self) -> None:
        obj = object()
        self.el = {
            123: 'abc',
            'abc': "ghi",
            obj: True,
            'none': None,
            'list': [1, 'two']
        }
        self.p = TimedPool(initial=self.el)

    def tearDown(self) -> None:
        self.p.stop()
        return super().tearDown()

    def test_is_dict(self):
        self.assertIsInstance(self.p, dict)

    def test_clear(self):
        self.p.clear()
        self.assertEqual(len(self.p), 0)

    def test_popitem(self):
        k, v = self.p.popitem()
        self.assertEqual(self.el[k], v)
        self.assertFalse(k in self.p)

    def test_keys(self):
        keys = self.p.keys()
        self.assertEqual(self.el.keys(), keys)

    def test_len(self):
        self.assertEqual(len(self.p), len(self.el))

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

    def test_delitem(self):
        k, _ = list(self.el.items())[0]
        self.assertTrue(k in self.p)
        del self.p[k]
        self.assertFalse(k in self.p)

    def test_iter(self):
        it = zip(iter(self.p), iter(self.el), strict=True)

        for a, b in it:
            self.assertEqual(a, b)

    def test_reversed(self):
        it = zip(reversed(self.p), reversed(self.el), strict=True)

        for a, b in it:
            self.assertEqual(a, b)

    def test_list(self):
        self.assertListEqual(list(self.p), list(self.el))

    def test_contain(self):
        k, _ = list(self.el.items())[0]
        self.assertTrue(k in self.p)
        self.assertFalse('Not' in self.p)

    def test_not_contain(self):
        k, _ = list(self.el.items())[0]
        self.assertFalse(k not in self.p)
        self.assertTrue('Not' not in self.p)

    def test_from_keys(self):
        keys = list(self.el.keys())
        p = TimedPool.fromkeys(keys)
        for key in keys:
            self.assertIsNone(p[key])
        p.stop()

    def test_from_keys_value(self):
        keys = list(self.el.keys())
        p = TimedPool.fromkeys(keys, 7)
        for key in keys:
            self.assertEqual(p[key], 7)
        p.stop()

    def test_get(self):
        k, v = list(self.el.items())[0]
        self.assertEqual(self.p.get(k), v)
        self.assertIsNone(self.p.get('Not'))

    def test_get_default(self):
        k, v = list(self.el.items())[0]
        self.assertEqual(self.p.get(k, 'def'), v)
        self.assertEqual(self.p.get('Not', 'def'), 'def')

    def test_pop(self):
        k, v = list(self.el.items())[0]
        popped = self.p.pop(k)
        self.assertEqual(v, popped)

        with self.assertRaises(KeyError):
            self.p.pop('Not')

    def test_pop_default(self):
        k, v = list(self.el.items())[0]
        popped = self.p.pop(k, 'def')
        self.assertEqual(v, popped)

        self.assertEqual(self.p.pop('Not', 'def'), 'def')
