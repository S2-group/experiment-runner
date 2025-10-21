# cython: language_level=3
from multiprocessing import Pool
from math import sqrt
from sys import argv
cimport cython

cdef double eval_A(int i, int j):
    return 1.0 / ((i + j) * (i + j + 1) / 2 + i + 1)

@cython.boundscheck(False)
@cython.wraparound(False)
cdef double part_A_times_u_cython(int i, list u):
    cdef double partial_sum = 0
    cdef int j
    cdef double u_j
    cdef int u_len = len(u)
    
    for j in range(u_len):
        u_j = u[j]
        partial_sum += eval_A(i, j) * u_j
    return partial_sum

@cython.boundscheck(False)
@cython.wraparound(False)
cdef double part_At_times_u_cython(int i, list u):
    cdef double partial_sum = 0
    cdef int j
    cdef double u_j
    cdef int u_len = len(u)
    
    for j in range(u_len):
        u_j = u[j]
        partial_sum += eval_A(j, i) * u_j
    return partial_sum

def eval_A_times_u(u):
    args = ((i, u) for i in range(len(u)))
    return pool.map(part_A_times_u, args)

def eval_At_times_u(u):
    args = ((i, u) for i in range(len(u)))
    return pool.map(part_At_times_u, args)

def eval_AtA_times_u(u):
    return eval_At_times_u(eval_A_times_u(u))

def part_A_times_u(args):
    i, u = args
    return part_A_times_u_cython(i, u)

def part_At_times_u(args):
    i, u = args
    return part_At_times_u_cython(i, u)

def main():
    cdef int n = int(argv[1])
    cdef list u = [1] * n
    cdef list v
    cdef int dummy
    cdef double vBv = 0
    cdef double vv = 0
    cdef double ue, ve

    for dummy in range(10):
        v = eval_AtA_times_u(u)
        u = eval_AtA_times_u(v)

    for ue, ve in zip(u, v):
        vBv += ue * ve
        vv += ve * ve

if __name__ == '__main__':
    import time

    pool = Pool(processes=4)
    n = 500

    start_time = time.time()
    print(f"Benchmark start: {start_time}")

    cold_start = time.time()
    argv = ['spectral_norm', str(n)]
    main()
    cold_end = time.time()
    cold_duration = cold_end - cold_start
    print(f"Cold start: {cold_start}")
    print(f"Cold end: {cold_end}")
    print(f"Cold duration: {cold_duration}")

    warm_start = time.time()
    main()
    warm_end = time.time()
    warm_duration = warm_end - warm_start
    print(f"Warm start: {warm_start}")
    print(f"Warm end: {warm_end}")
    print(f"Warm duration: {warm_duration}")