from multiprocessing import Pool
from math import sqrt
from sys import argv
from numba import jit
import numpy as np

@jit(nopython=True)
def eval_A(i, j):
    return 1.0 / ((i + j) * (i + j + 1) / 2 + i + 1)

@jit(nopython=True)
def eval_A_times_u_numba(u):
    n = len(u)
    result = np.zeros(n)
    for i in range(n):
        partial_sum = 0.0
        for j in range(n):
            partial_sum += eval_A(i, j) * u[j]
        result[i] = partial_sum
    return result

@jit(nopython=True)
def eval_At_times_u_numba(u):
    n = len(u)
    result = np.zeros(n)
    for i in range(n):
        partial_sum = 0.0
        for j in range(n):
            partial_sum += eval_A(j, i) * u[j]
        result[i] = partial_sum
    return result

@jit(nopython=True)
def eval_AtA_times_u_numba(u):
    return eval_At_times_u_numba(eval_A_times_u_numba(u))

@jit(nopython=True)
def spectral_norm_core(n):
    u = np.ones(n)
    
    for _ in range(10):
        v = eval_AtA_times_u_numba(u)
        u = eval_AtA_times_u_numba(v)

    vBv = 0.0
    vv = 0.0

    for i in range(len(u)):
        vBv += u[i] * v[i]
        vv += v[i] * v[i]

    return sqrt(vBv/vv)

def part_A_times_u(args):
    i, u = args
    partial_sum = 0
    for j, u_j in enumerate(u):
        partial_sum += eval_A(i, j) * u_j
    return partial_sum

def part_At_times_u(args):
    i, u = args
    partial_sum = 0
    for j, u_j in enumerate(u):
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

def main():
    n = int(argv[1])
    result = spectral_norm_core(n)

if __name__ == '__main__':
    import time

    # pool = Pool(processes=4)
    n = 600

    argv = ['spectral_norm', str(n)]
    with Pool(processes=4) as pool:
        main()
    print(time.time())

    with Pool(processes=4) as pool:
        main()
