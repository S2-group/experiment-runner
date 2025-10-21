import pyperf
from numba import jit

@jit(nopython=True)
def fannkuch(n):
    count = [i for i in range(1, n + 1)]
    max_flips = 0
    m = n - 1
    r = n
    perm1 = [i for i in range(n)]
    perm = [i for i in range(n)]

    while True:
        while r != 1:
            count[r - 1] = r
            r -= 1

        if perm1[0] != 0 and perm1[m] != m:
            for i in range(n):
                perm[i] = perm1[i]
            flips_count = 0
            k = perm[0]
            while k:
                for i in range((k + 1) // 2):
                    temp = perm[i]
                    perm[i] = perm[k - i]
                    perm[k - i] = temp
                flips_count += 1
                k = perm[0]

            if flips_count > max_flips:
                max_flips = flips_count

        while r != n:
            temp = perm1[0]
            for i in range(r):
                perm1[i] = perm1[i + 1]
            perm1[r] = temp
            count[r] -= 1
            if count[r] > 0:
                break
            r += 1
        else:
            return max_flips

DEFAULT_ARG = 9

if __name__ == "__main__":
    import time

    arg = DEFAULT_ARG

    start_time = time.time()
    print(f"Benchmark start: {start_time}")

    cold_start = time.time()
    fannkuch(arg)
    cold_end = time.time()
    cold_duration = cold_end - cold_start
    print(f"Cold start: {cold_start}")
    print(f"Cold end: {cold_end}")
    print(f"Cold duration: {cold_duration}")

    warm_start = time.time()
    fannkuch(arg)
    warm_end = time.time()
    warm_duration = warm_end - warm_start
    print(f"Warm start: {warm_start}")
    print(f"Warm end: {warm_end}")
    print(f"Warm duration: {warm_duration}")