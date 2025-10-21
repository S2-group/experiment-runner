# cython: language_level=3
import pyperf

cdef int fannkuch_cython(int n):
    cdef list count = list(range(1, n + 1))
    cdef int max_flips = 0
    cdef int m = n - 1
    cdef int r = n
    cdef list perm1 = list(range(n))
    cdef list perm = list(range(n))
    cdef int flips_count, k

    while 1:
        while r != 1:
            count[r - 1] = r
            r -= 1

        if perm1[0] != 0 and perm1[m] != m:
            perm = perm1[:]
            flips_count = 0
            k = perm[0]
            while k:
                perm[:k + 1] = perm[k::-1]
                flips_count += 1
                k = perm[0]

            if flips_count > max_flips:
                max_flips = flips_count

        while r != n:
            perm1.insert(r, perm1.pop(0))
            count[r] -= 1
            if count[r] > 0:
                break
            r += 1
        else:
            return max_flips

def fannkuch(n):
    return fannkuch_cython(n)

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