# cython: language_level=3
from __future__ import annotations
from typing import List

ctypedef list[int] IntList

cdef list merge(IntList left_half, IntList right_half):
    cdef int left_len = len(left_half)
    cdef int right_len = len(right_half)
    cdef list sorted_array = [None] * (left_len + right_len)
    
    cdef int pointer1 = 0
    cdef int pointer2 = 0
    cdef int index = 0

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

cdef list merge_sort(IntList array):
    cdef int length = len(array)
    if length <= 1:
        return array
        
    cdef int middle = 0 + (length - 0) // 2
    cdef list left_half = array[:middle]
    cdef list right_half = array[middle:]

    return merge(merge_sort(left_half), merge_sort(right_half))

def merge_sort_public(array: list) -> list:
    return merge_sort(array)

if __name__ == "__main__":
    import doctest
    doctest.testmod()