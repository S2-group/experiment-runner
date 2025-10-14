"""
Optimized (Unroll-4) version of 0-N Knapsack Problem.
Reference baseline: recursive knapsack with lru_cache.
Optimization:
 - replaces recursion with iterative DP table (bottom-up)
 - unrolls inner loop by 4 items per iteration to reduce overhead
"""

from __future__ import annotations


def knapsack_iterative_unroll4(
    capacity: int,
    weights: list[int],
    values: list[int],
    allow_repetition=False,
) -> int:
    """
    Iterative DP version of knapsack with manual loop unrolling.

    >>> cap = 50
    >>> val = [60, 100, 120]
    >>> w = [10, 20, 30]
    >>> knapsack_iterative_unroll4(cap, w, val)
    220
    >>> knapsack_iterative_unroll4(cap, w, val, True)
    300
    """
    n = len(values)
    # dp[i][c] = max value for first i items and capacity c
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    if not allow_repetition:
        # 0-1 Knapsack
        for i in range(1, n + 1):
            wt = weights[i - 1]
            val = values[i - 1]
            c = 0
            # unroll loop by 4
            while c + 3 <= capacity:
                dp[i][c] = dp[i - 1][c]
                dp[i][c + 1] = dp[i - 1][c + 1]
                dp[i][c + 2] = dp[i - 1][c + 2]
                dp[i][c + 3] = dp[i - 1][c + 3]
                if wt <= c:
                    dp[i][c] = max(dp[i][c], val + dp[i - 1][c - wt])
                if wt <= c + 1:
                    dp[i][c + 1] = max(dp[i][c + 1], val + dp[i - 1][c + 1 - wt])
                if wt <= c + 2:
                    dp[i][c + 2] = max(dp[i][c + 2], val + dp[i - 1][c + 2 - wt])
                if wt <= c + 3:
                    dp[i][c + 3] = max(dp[i][c + 3], val + dp[i - 1][c + 3 - wt])
                c += 4
            while c <= capacity:
                dp[i][c] = dp[i - 1][c]
                if wt <= c:
                    dp[i][c] = max(dp[i][c], val + dp[i - 1][c - wt])
                c += 1
    else:
        # Unbounded (0-N) Knapsack
        dp = [0] * (capacity + 1)
        for i in range(n):
            wt = weights[i]
            val = values[i]
            c = wt
            while c + 3 <= capacity:
                # unrolled updates
                dp[c] = max(dp[c], val + dp[c - wt])
                dp[c + 1] = max(dp[c + 1], val + dp[c + 1 - wt])
                dp[c + 2] = max(dp[c + 2], val + dp[c + 2 - wt])
                dp[c + 3] = max(dp[c + 3], val + dp[c + 3 - wt])
                c += 4
            while c <= capacity:
                dp[c] = max(dp[c], val + dp[c - wt])
                c += 1
        return dp[capacity]

    return dp[n][capacity]


if __name__ == "__main__":
    import doctest

    doctest.testmod()

    # quick manual check
    cap = 50
    val = [60, 100, 120]
    w = [10, 20, 30]
    print("0-1 Knapsack:", knapsack_iterative_unroll4(cap, w, val))
    print("0-N Knapsack:", knapsack_iterative_unroll4(cap, w, val, True))
