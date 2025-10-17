import random, time

def merge(left_half, right_half):
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


def merge_sort(array):
    if len(array) <= 1:
        return array
    mid = len(array) // 2
    left_half = array[:mid]
    right_half = array[mid:]
    return merge(merge_sort(left_half), merge_sort(right_half))


if __name__ == "__main__":
    arr = [random.randint(0, 100000) for _ in range(5000)]
    start = time.time()
    while time.time() - start < 30:     # run for 30 seconds
        merge_sort(arr)
