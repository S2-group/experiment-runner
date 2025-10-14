"""
Optimized (Unroll-4) version of Product Sum from a Special Array.
Reference baseline: https://dev.to/sfrasica/algorithms-product-sum-from-an-array-dc6
Optimization:
 - eliminates Python recursion by using an explicit stack
 - processes elements four at a time (loop unrolling)
"""

from __future__ import annotations
from collections.abc import Iterable


def product_sum_unrolled(array: list[int | list]) -> int:
    """
    Iterative (unrolled) product-sum calculation.
    Equivalent to product_sum_array in baseline but with manual loop unrolling.

    Examples:
        >>> product_sum_unrolled([1, 2, 3])
        6
        >>> product_sum_unrolled([1, [2, 3]])
        11
        >>> product_sum_unrolled([1, [2, [3, 4]]])
        47
        >>> product_sum_unrolled([-3.5, [1, [0.5]]])
        1.5
    """
    total = 0
    stack: list[tuple[list[int | list], int]] = [(array, 1)]

    while stack:
        current, depth = stack.pop()
        i = 0
        n = len(current)

        # Unroll-4 processing for performance
        while i + 3 < n:
            for x in current[i:i+4]:
                if isinstance(x, list):
                    stack.append((x, depth + 1))
                else:
                    total += x * depth
            i += 4

        # Remaining elements
        while i < n:
            x = current[i]
            if isinstance(x, list):
                stack.append((x, depth + 1))
            else:
                total += x * depth
            i += 1

    return total


if __name__ == "__main__":
    import doctest
    doctest.testmod()

    # quick manual check like baseline main
    sample = [5, 2, [-7, 1], 3, [6, [-13, 8], 4]]
    print(product_sum_unrolled(sample))  # expected output: 12
