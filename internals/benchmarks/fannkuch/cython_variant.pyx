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

    fannkuch(arg)
    print(time.time())
    fannkuch(arg)