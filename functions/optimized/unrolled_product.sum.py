"""
Optimized (Unroll-4) version of Product Sum from a Special Array.
Reference baseline: recursive product_sum_array().
Optimization:
 - processes elements four at a time (loop unrolling)
 - correctly handles depth multipliers
"""

from __future__ import annotations
from collections.abc import Iterable


def product_sum(arr: list[int | list], depth: int) -> float:
    """
    Helper function with loop unrolling optimization.
    """
    total_sum = 0.0
    i = 0
    n = len(arr)
    
    # unrolled by 4 elements at a time - explicitly process 4 elements
    while i + 3 < n:
        # Element 0
        ele0 = arr[i]
        total_sum += product_sum(ele0, depth + 1) if isinstance(ele0, list) else ele0
        # Element 1
        ele1 = arr[i + 1]
        total_sum += product_sum(ele1, depth + 1) if isinstance(ele1, list) else ele1
        # Element 2
        ele2 = arr[i + 2]
        total_sum += product_sum(ele2, depth + 1) if isinstance(ele2, list) else ele2
        # Element 3
        ele3 = arr[i + 3]
        total_sum += product_sum(ele3, depth + 1) if isinstance(ele3, list) else ele3
        i += 4
    
    # handle remaining elements (0-3 elements)
    while i < n:
        ele = arr[i]
        total_sum += product_sum(ele, depth + 1) if isinstance(ele, list) else ele
        i += 1
    
    return total_sum * depth


def product_sum_unrolled(array: list[int | list]) -> float:
    """
    Loop-unrolled product-sum equivalent to baseline.

    Examples:
        >>> product_sum_unrolled([1, 2, 3])
        6.0
        >>> product_sum_unrolled([1, [2, 3]])
        11.0
        >>> product_sum_unrolled([1, [2, [3, 4]]])
        47.0
        >>> product_sum_unrolled([-3.5, [1, [0.5]]])
        1.5
    """
    return product_sum(array, 1)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # Manual sanity check
    print(product_sum_unrolled([5, 2, [-7, 1], 3, [6, [-13, 8], 4]]))  # should print -12
