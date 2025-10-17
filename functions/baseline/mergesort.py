import random, time

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
    mid = len(array) // 2
    left_half = array[:mid]
    right_half = array[mid:]
    return merge(merge_sort(left_half), merge_sort(right_half))


if __name__ == "__main__":
    target_time = 30  # seconds
    n = 5000
    elapsed = 0

    print("Finding input size for ~30 seconds runtime...")
    while elapsed < target_time:
        arr = [random.randint(0, 100000) for _ in range(n)]
        start = time.time()
        merge_sort(arr)
        elapsed = time.time() - start
        print(f"Input size: {n}, Time: {elapsed:.2f} s")

        if elapsed < target_time:
            # Exponentially increase size
            n = int(n * 1.5)
        elif elapsed > target_time * 1.5:
            # Too high, reduce step if we overshoot too much
            n = int(n * 0.9)
            elapsed = 0  # re-test
        else:
            break

    print(f"\n✅ Final input size: {n} (runtime ≈ {elapsed:.2f} s)")
