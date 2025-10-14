from collections.abc import Sequence


# -------------------------------------------------------------
# UNROLLED (Unroll-4) VERSION OF MAXIMUM SUBARRAY
# -------------------------------------------------------------
def unroll4_max_subarray(
    arr: Sequence[float], low: int, high: int
) -> tuple[int | None, int | None, float]:
    """
    Divide-and-conquer maximum subarray (unrolled version).
    Loop unrolling is applied in the cross-sum computation to handle
    four elements per iteration.
    """
    # Handle empty or single-element cases
    if not arr:
        return None, None, 0
    if low == high:
        return low, high, arr[low]

    mid = (low + high) // 2

    # Recursively find max subarray on left and right halves
    left_low, left_high, left_sum = unroll4_max_subarray(arr, low, mid)
    right_low, right_high, right_sum = unroll4_max_subarray(arr, mid + 1, high)

    # Compute max crossing subarray using unrolled helper
    cross_left, cross_right, cross_sum = unroll4_max_cross_sum(arr, low, mid, high)

    # Return whichever side has the largest sum
    if left_sum >= right_sum and left_sum >= cross_sum:
        return left_low, left_high, left_sum
    elif right_sum >= left_sum and right_sum >= cross_sum:
        return right_low, right_high, right_sum
    else:
        return cross_left, cross_right, cross_sum


def unroll4_max_cross_sum(
    arr: Sequence[float], low: int, mid: int, high: int
) -> tuple[int, int, float]:
    """
    Helper for unrolled max_subarray:
    computes max crossing subarray sum with 4-element loop unrolling.
    """
    left_sum = float("-inf")
    right_sum = float("-inf")
    max_left = -1
    max_right = -1

    # ---------- LEFT SIDE ----------
    summ = 0
    i = mid
    # Unrolled loop: 4 steps per iteration
    while i - 3 >= low:
        for j in (i, i - 1, i - 2, i - 3):
            summ += arr[j]
            if summ > left_sum:
                left_sum = summ
                max_left = j
        i -= 4

    # Handle remaining elements (if <4 left)
    while i >= low:
        summ += arr[i]
        if summ > left_sum:
            left_sum = summ
            max_left = i
        i -= 1

    # ---------- RIGHT SIDE ----------
    summ = 0
    i = mid + 1
    # Unrolled loop: 4 steps per iteration
    while i + 3 <= high:
        for j in (i, i + 1, i + 2, i + 3):
            summ += arr[j]
            if summ > right_sum:
                right_sum = summ
                max_right = j
        i += 4

    # Handle remaining elements (if <4 left)
    while i <= high:
        summ += arr[i]
        if summ > right_sum:
            right_sum = summ
            max_right = i
        i += 1

    return max_left, max_right, left_sum + right_sum
