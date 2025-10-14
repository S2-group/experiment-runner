# baseline/mergesort.py: non-optimised
from __future__ import annotations

def merge(left_half: list, right_half: list) -> list:
    sorted_array = [None] * (len(right_half) + len(left_half))
    pointer1 = 0
    pointer2 = 0
    index = 0

    while pointer1 < len(left_half) and pointer2 < len(right_half):
        if left_half[pointer1] < right_half[pointer2]:
            sorted_array[index] = left_half[pointer1]
            pointer1 += 1
        else:
            sorted_array[index] = right_half[pointer2]
            pointer2 += 1
        index += 1

    while pointer1 < len(left_half):
        sorted_array[index] = left_half[pointer1]
        pointer1 += 1
        index += 1

    while pointer2 < len(right_half):
        sorted_array[index] = right_half[pointer2]
        pointer2 += 1
        index += 1

    return sorted_array


def merge_sort(array: list) -> list:
    if len(array) <= 1:
        return array

    middle = len(array) // 2
    left_half = array[:middle]
    right_half = array[middle:]

    return merge(merge_sort(left_half), merge_sort(right_half))


if __name__ == "__main__":
    import random
    arr = [random.randint(0, 100000) for _ in range(5000)]
    merge_sort(arr)
