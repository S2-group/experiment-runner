from collections.abc import MutableSequence
from typing import Any, Protocol, TypeVar
from numba import jit
from numba.typed import List
import numba

class Comparable(Protocol):
    def __lt__(self, other: Any, /) -> bool: ...

T = TypeVar("T", bound=Comparable)

@jit(nopython=True)
def insertion_sort_core(collection):
    for insert_index in range(1, len(collection)):
        insert_value = collection[insert_index]
        while insert_index > 0 and insert_value < collection[insert_index - 1]:
            collection[insert_index] = collection[insert_index - 1]
            insert_index -= 1
        collection[insert_index] = insert_value
    return collection

def insertion_sort(collection: MutableSequence[T]) -> MutableSequence[T]:
    if not collection:
        return collection
    
    if all(isinstance(x, (int, float)) for x in collection):
        typed_list = List()
        for item in collection:
            typed_list.append(item)
        result = insertion_sort_core(typed_list)
        return [x for x in result]
    else:
        for insert_index in range(1, len(collection)):
            insert_value = collection[insert_index]
            while insert_index > 0 and insert_value < collection[insert_index - 1]:
                collection[insert_index] = collection[insert_index - 1]
                insert_index -= 1
            collection[insert_index] = insert_value
        return collection

if __name__ == "__main__":
    import time
    import random

    unsorted = list(range(5000))
    random.shuffle(unsorted)

    start_time = time.time()
    print(f"Benchmark start: {start_time}")

    cold_start = time.time()
    insertion_sort(unsorted.copy())
    cold_end = time.time()
    cold_duration = cold_end - cold_start
    print(f"Cold start: {cold_start}")
    print(f"Cold end: {cold_end}")
    print(f"Cold duration: {cold_duration}")

    warm_start = time.time()
    insertion_sort(unsorted.copy())
    warm_end = time.time()
    warm_duration = warm_end - warm_start
    print(f"Warm start: {warm_start}")
    print(f"Warm end: {warm_end}")
    print(f"Warm duration: {warm_duration}")