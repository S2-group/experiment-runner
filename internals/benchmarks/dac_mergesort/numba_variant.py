from __future__ import annotations
from numba import jit
from numba.typed import List
import numba

@jit(nopython=True)
def merge(left_half, right_half):
    left_len = len(left_half)
    right_len = len(right_half)
    sorted_array = [0] * (left_len + right_len)
    
    pointer1 = 0
    pointer2 = 0
    index = 0

    while pointer1 < left_len and pointer2 < right_len:
        if left_half[pointer1] < right_half[pointer2]:
            sorted_array[index] = left_half[pointer1]
            pointer1 += 1
            index += 1
        else:
            sorted_array[index] = right_half[pointer2]
            pointer2 += 1
            index += 1
    while pointer1 < left_len:
        sorted_array[index] = left_half[pointer1]
        pointer1 += 1
        index += 1

    while pointer2 < right_len:
        sorted_array[index] = right_half[pointer2]
        pointer2 += 1
        index += 1

    return sorted_array

@jit(nopython=True)
def merge_sort(array):
    if len(array) <= 1:
        return array
    middle = 0 + (len(array) - 0) // 2

    left_half = array[:middle]
    right_half = array[middle:]

    return merge(merge_sort(left_half), merge_sort(right_half))

def merge_sort_public(array: list) -> list:
    if not array:
        return array
    typed_array = List()
    for item in array:
        typed_array.append(item)
    result = merge_sort(typed_array)
    return [x for x in result]

if __name__ == "__main__":
    import doctest
    doctest.testmod()