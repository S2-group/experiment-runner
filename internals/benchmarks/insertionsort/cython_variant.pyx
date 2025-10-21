# cython: language_level=3
from collections.abc import MutableSequence
from typing import Any, Protocol, TypeVar

class Comparable(Protocol):
    def __lt__(self, other: Any, /) -> bool: ...

T = TypeVar("T", bound=Comparable)

cdef object insertion_sort_cython(list collection):
    cdef int insert_index
    cdef object insert_value
    cdef int length = len(collection)

    for insert_index in range(1, length):
        insert_value = collection[insert_index]
        while insert_index > 0 and insert_value < collection[insert_index - 1]:
            collection[insert_index] = collection[insert_index - 1]
            insert_index -= 1
        collection[insert_index] = insert_value
    return collection

def insertion_sort(collection: MutableSequence[T]) -> MutableSequence[T]:
    return insertion_sort_cython(list(collection))

if __name__ == "__main__":
    import time
    import random

    unsorted = list(range(5000))
    random.shuffle(unsorted)

    insertion_sort(unsorted.copy())
    print(time.time())
    insertion_sort(unsorted.copy())