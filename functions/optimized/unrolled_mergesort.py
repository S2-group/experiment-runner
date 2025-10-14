# optimized/mergesort.py: loop unrolled 4
from __future__ import annotations

def merge(left_half: list, right_half: list) -> list:
    sorted_array = [None] * (len(right_half) + len(left_half))
    pointer1 = 0
    pointer2 = 0
    index = 0
    len_left = len(left_half)
    len_right = len(right_half)

    # Loop unrolling by 4
    while pointer1 + 3 < len_left and pointer2 + 3 < len_right:
        for _ in range(4):
            if left_half[pointer1] < right_half[pointer2]:
                sorted_array[index] = left_half[pointer1]
                pointer1 += 1
            else:
                sorted_array[index] = right_half[pointer2]
                pointer2 += 1
            index += 1

    # Normal merge for remaining elements
    while pointer1 < len_left and pointer2 < len_right:
        if left_half[pointer1] < right_half[pointer2]:
            sorted_array[index] = left_half[pointer1]
            pointer1 += 1
        else:
            sorted_array[index] = right_half[pointer2]
            pointer2 += 1
        index += 1

    while pointer1 < len_left:
        sorted_array[index] = left_half[pointer1]
        pointer1 += 1
        index += 1

    while pointer2 < len_right:
        sorted_array[index] = right_half[pointer2]
        pointer2 += 1
        index += 1

    return sorted_array


def merge_sort(array: list) -> list:
    if len(array) <= 1:
        return array
    middle = len(array) // 2
    return merge(merge_sort(array[:middle]), merge_sort(array[middle:]))


if __name__ == "__main__":
    import random
    import time

    arr = [random.randint(0, 100000) for _ in range(5000)]
    start = time.time()
    sorted_arr = merge_sort(arr)
    end = time.time()
    print(f"Execution time: {end - start:.5f} seconds")
