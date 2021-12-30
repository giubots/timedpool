# timedpool
Python library adding a dictionary with a maximum size and whose elements are deleted after a delay.

## Installation

Run: `pip install timedpool`

## Usage

TimedPool is a dict with a maximum size whose elements are deleted after a delay.

This object can be used as a dictionary:
```python
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

This object supports all the methods of a python dict with the following exceptions:
* copy
* setdefault
* update
* values
* items

# Implementation

The implementation extends a python dict. A routine is run on another thread to periodically scan the elements and remove those that are expired.

This implies that expired elements will be still available until the cleaning routine is run.

# Contribute

If you find a bug, have a feature request or suggestions, please open an issue on github.
