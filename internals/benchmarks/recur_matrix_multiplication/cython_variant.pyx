# cython: language_level=3
cimport cython
from typing import List

ctypedef list[list[int]] Matrix

matrix_1_to_4 = [
    [1, 2],
    [3, 4],
]

matrix_5_to_8 = [
    [5, 6],
    [7, 8],
]

matrix_5_to_9_high = [
    [5, 6],
    [7, 8],
    [9],
]

matrix_5_to_9_wide = [
    [5, 6],
    [7, 8, 9],
]

matrix_count_up = [
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9, 10, 11, 12],
    [13, 14, 15, 16],
]

matrix_unordered = [
    [5, 8, 1, 2],
    [6, 7, 3, 0],
    [4, 5, 9, 1],
    [2, 6, 10, 14],
]

matrices = (
    matrix_1_to_4,
    matrix_5_to_8,
    matrix_5_to_9_high,
    matrix_5_to_9_wide,
    matrix_count_up,
    matrix_unordered,
)

cdef bint is_square_cython(list matrix):
    cdef int len_matrix = len(matrix)
    cdef list row
    for row in matrix:
        if len(row) != len_matrix:
            return False
    return True

def is_square(matrix: Matrix) -> bool:
    return is_square_cython(matrix)

cdef list matrix_multiply_cython(list matrix_a, list matrix_b):
    cdef list result = []
    cdef list row, col
    cdef int sum_val, a, b
    
    for row in matrix_a:
        result_row = []
        for col in zip(*matrix_b):
            sum_val = 0
            for a, b in zip(row, col):
                sum_val += a * b
            result_row.append(sum_val)
        result.append(result_row)
    return result

def matrix_multiply(matrix_a: Matrix, matrix_b: Matrix) -> Matrix:
    return matrix_multiply_cython(matrix_a, matrix_b)

@cython.boundscheck(False)
@cython.wraparound(False)
cdef void multiply_recursive(int i_loop, int j_loop, int k_loop, 
                            list matrix_a, list matrix_b, list result):
    cdef int a_len = len(matrix_a)
    cdef int b_cols = len(matrix_b[0])
    cdef int b_len = len(matrix_b)
    
    if i_loop >= a_len:
        return
    if j_loop >= b_cols:
        return multiply_recursive(i_loop + 1, 0, 0, matrix_a, matrix_b, result)
    if k_loop >= b_len:
        return multiply_recursive(i_loop, j_loop + 1, 0, matrix_a, matrix_b, result)
    
    result[i_loop][j_loop] += matrix_a[i_loop][k_loop] * matrix_b[k_loop][j_loop]
    return multiply_recursive(i_loop, j_loop, k_loop + 1, matrix_a, matrix_b, result)

cdef list matrix_multiply_recursive_cython(list matrix_a, list matrix_b):
    if not matrix_a or not matrix_b:
        return []
    if not (len(matrix_a) == len(matrix_b) and 
            is_square_cython(matrix_a) and is_square_cython(matrix_b)):
        raise ValueError("Invalid matrix dimensions")

    cdef list result = [[0] * len(matrix_b[0]) for _ in range(len(matrix_a))]
    multiply_recursive(0, 0, 0, matrix_a, matrix_b, result)
    return result

def matrix_multiply_recursive(matrix_a: Matrix, matrix_b: Matrix) -> Matrix:
    return matrix_multiply_recursive_cython(matrix_a, matrix_b)

if __name__ == "__main__":
    from doctest import testmod

    failure_count, test_count = testmod()
    if not failure_count:
        matrix_a = matrices[0]
        for matrix_b in matrices[1:]:
            print("Multiplying:")
            for row in matrix_a:
                print(row)
            print("By:")
            for row in matrix_b:
                print(row)
            print("Result:")
            try:
                result = matrix_multiply_recursive(matrix_a, matrix_b)
                for row in result:
                    print(row)
                assert result == matrix_multiply(matrix_a, matrix_b)
            except ValueError as e:
                print(f"{e!r}")
            print()
            matrix_a = matrix_b

    print("Benchmark:")
    from functools import partial
    from timeit import timeit

    mytimeit = partial(timeit, globals=globals(), number=100_000)
    for func in ("matrix_multiply", "matrix_multiply_recursive"):
        print(f"{func:>25}(): {mytimeit(f'{func}(matrix_count_up, matrix_unordered)')}")