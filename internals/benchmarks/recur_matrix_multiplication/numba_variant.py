from typing import List
from numba import jit
from numba.typed import List as TypedList
import numba

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

@jit(nopython=True)
def is_square_numba(matrix):
    if len(matrix) == 0:
        return True
    len_matrix = len(matrix)
    for i in range(len(matrix)):
        if len(matrix[i]) != len_matrix:
            return False
    return True

def is_square(matrix) -> bool:
    if not matrix:
        return True
    typed_matrix = TypedList()
    for row in matrix:
        typed_row = TypedList()
        for item in row:
            typed_row.append(item)
        typed_matrix.append(typed_row)
    return is_square_numba(typed_matrix)

@jit(nopython=True)
def matrix_multiply_numba(matrix_a, matrix_b):
    rows_a = len(matrix_a)
    cols_a = len(matrix_a[0]) if rows_a > 0 else 0
    rows_b = len(matrix_b)
    cols_b = len(matrix_b[0]) if rows_b > 0 else 0
    
    if cols_a != rows_b:
        return TypedList.empty_list(TypedList.empty_list(numba.types.int64))
    
    result = TypedList()
    for i in range(rows_a):
        row = TypedList()
        for j in range(cols_b):
            sum_val = 0
            for k in range(cols_a):
                sum_val += matrix_a[i][k] * matrix_b[k][j]
            row.append(sum_val)
        result.append(row)
    return result

def matrix_multiply(matrix_a, matrix_b):
    if not matrix_a or not matrix_b:
        return []
    
    typed_a = TypedList()
    typed_b = TypedList()
    
    for row in matrix_a:
        typed_row = TypedList()
        for item in row:
            typed_row.append(item)
        typed_a.append(typed_row)
    
    for row in matrix_b:
        typed_row = TypedList()
        for item in row:
            typed_row.append(item)
        typed_b.append(typed_row)
    
    result = matrix_multiply_numba(typed_a, typed_b)
    return [[result[i][j] for j in range(len(result[i]))] for i in range(len(result))]

@jit(nopython=True)
def multiply_recursive_numba(i_loop, j_loop, k_loop, matrix_a, matrix_b, result):
    if i_loop >= len(matrix_a):
        return
    if j_loop >= len(matrix_b[0]):
        return multiply_recursive_numba(i_loop + 1, 0, 0, matrix_a, matrix_b, result)
    if k_loop >= len(matrix_b):
        return multiply_recursive_numba(i_loop, j_loop + 1, 0, matrix_a, matrix_b, result)
    
    result[i_loop][j_loop] += matrix_a[i_loop][k_loop] * matrix_b[k_loop][j_loop]
    return multiply_recursive_numba(i_loop, j_loop, k_loop + 1, matrix_a, matrix_b, result)

@jit(nopython=True)
def matrix_multiply_recursive_numba(matrix_a, matrix_b):
    if len(matrix_a) == 0 or len(matrix_b) == 0:
        return TypedList.empty_list(TypedList.empty_list(numba.types.int64))
    
    if not (len(matrix_a) == len(matrix_b) and 
            is_square_numba(matrix_a) and is_square_numba(matrix_b)):
        return TypedList.empty_list(TypedList.empty_list(numba.types.int64))

    result = TypedList()
    for i in range(len(matrix_a)):
        row = TypedList()
        for j in range(len(matrix_b[0])):
            row.append(0)
        result.append(row)
    
    multiply_recursive_numba(0, 0, 0, matrix_a, matrix_b, result)
    return result

def matrix_multiply_recursive(matrix_a, matrix_b):
    if not matrix_a or not matrix_b:
        return []
    if not all(
        (len(matrix_a) == len(matrix_b), is_square(matrix_a), is_square(matrix_b))
    ):
        raise ValueError("Invalid matrix dimensions")

    typed_a = TypedList()
    typed_b = TypedList()
    
    for row in matrix_a:
        typed_row = TypedList()
        for item in row:
            typed_row.append(item)
        typed_a.append(typed_row)
    
    for row in matrix_b:
        typed_row = TypedList()
        for item in row:
            typed_row.append(item)
        typed_b.append(typed_row)
    
    result = matrix_multiply_recursive_numba(typed_a, typed_b)
    
    if len(result) == 0:
        raise ValueError("Invalid matrix dimensions")
    
    return [[result[i][j] for j in range(len(result[i]))] for i in range(len(result))]

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