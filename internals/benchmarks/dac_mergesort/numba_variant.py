from __future__ import annotations
from numba import jit
from numba.typed import List
import numba


@jit(nopython=True)
def merge(left_half, right_half):
    left_len = len(left_half)
    right_len = len(right_half)
    sorted_array = List.empty_list(numba.int64)

    pointer1 = 0
    pointer2 = 0

    while pointer1 < left_len and pointer2 < right_len:
        if left_half[pointer1] < right_half[pointer2]:
            sorted_array.append(left_half[pointer1])
            pointer1 += 1
        else:
            sorted_array.append(right_half[pointer2])
            pointer2 += 1

    while pointer1 < left_len:
        sorted_array.append(left_half[pointer1])
        pointer1 += 1

    while pointer2 < right_len:
        sorted_array.append(right_half[pointer2])
        pointer2 += 1

    return sorted_array


@jit(nopython=True)
def merge_sort(array):
    if len(array) <= 1:
        return array

    middle = len(array) // 2
    left_half = array[:middle]
    right_half = array[middle:]

    merged = merge(merge_sort(left_half), merge_sort(right_half))
    return merged


def merge_sort_public(array: list[int]) -> list[int]:
    if not array:
        return array

    typed_array = List.empty_list(numba.int64)
    for item in array:
        typed_array.append(item)

    result = merge_sort(typed_array)
    return [x for x in result]


if __name__ == "__main__":
    import time
    import random

    array = list(range(10000))
    random.shuffle(array)

    merge_sort_public(array.copy())  # compile first
    start = time.time()
    print(time.time())
    merge_sort_public(array.copy())
    end = time.time()

