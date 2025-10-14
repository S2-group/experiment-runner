from __future__ import annotations
import math

# -------------------------------
# Optimized (Unroll-4) version
# -------------------------------

def default_matrix_multiplication(a: list, b: list) -> list:
    """
    Unrolled version for 2x2 matrices
    """
    if len(a) != 2 or len(a[0]) != 2 or len(b) != 2 or len(b[0]) != 2:
        raise Exception("Matrices are not 2x2")

    # manually unrolled to avoid inner loops
    a00, a01 = a[0]
    a10, a11 = a[1]
    b00, b01 = b[0]
    b10, b11 = b[1]

    c00 = a00 * b00 + a01 * b10
    c01 = a00 * b01 + a01 * b11
    c10 = a10 * b00 + a11 * b10
    c11 = a10 * b01 + a11 * b11

    return [[c00, c01], [c10, c11]]


def matrix_addition(matrix_a: list, matrix_b: list):
    """
    Element-wise matrix addition, unrolled by 4 columns when possible.
    """
    rows = len(matrix_a)
    cols = len(matrix_a[0])
    result = []
    for i in range(rows):
        row = []
        j = 0
        while j + 3 < cols:
            row.append(matrix_a[i][j] + matrix_b[i][j])
            row.append(matrix_a[i][j+1] + matrix_b[i][j+1])
            row.append(matrix_a[i][j+2] + matrix_b[i][j+2])
            row.append(matrix_a[i][j+3] + matrix_b[i][j+3])
            j += 4
        while j < cols:
            row.append(matrix_a[i][j] + matrix_b[i][j])
            j += 1
        result.append(row)
    return result


def matrix_subtraction(matrix_a: list, matrix_b: list):
    """
    Element-wise matrix subtraction, unrolled by 4 columns when possible.
    """
    rows = len(matrix_a)
    cols = len(matrix_a[0])
    result = []
    for i in range(rows):
        row = []
        j = 0
        while j + 3 < cols:
            row.append(matrix_a[i][j] - matrix_b[i][j])
            row.append(matrix_a[i][j+1] - matrix_b[i][j+1])
            row.append(matrix_a[i][j+2] - matrix_b[i][j+2])
            row.append(matrix_a[i][j+3] - matrix_b[i][j+3])
            j += 4
        while j < cols:
            row.append(matrix_a[i][j] - matrix_b[i][j])
            j += 1
        result.append(row)
    return result


def split_matrix(a: list) -> tuple[list, list, list, list]:
    """
    Same as baseline: split a square even-sized matrix into 4 quadrants.
    """
    if len(a) % 2 != 0 or len(a[0]) % 2 != 0:
        raise Exception("Odd matrices are not supported!")

    n = len(a)
    mid = n // 2
    top_left  = [row[:mid] for row in a[:mid]]
    top_right = [row[mid:] for row in a[:mid]]
    bot_left  = [row[:mid] for row in a[mid:]]
    bot_right = [row[mid:] for row in a[mid:]]
    return top_left, top_right, bot_left, bot_right


def matrix_dimensions(matrix: list) -> tuple[int, int]:
    return len(matrix), len(matrix[0])


def print_matrix(matrix: list) -> None:
    print("\n".join(str(line) for line in matrix))


def actual_strassen(matrix_a: list, matrix_b: list) -> list:
    """
    Recursive Strassen multiplication using optimized helpers.
    """
    if matrix_dimensions(matrix_a) == (2, 2):
        return default_matrix_multiplication(matrix_a, matrix_b)

    a, b, c, d = split_matrix(matrix_a)
    e, f, g, h = split_matrix(matrix_b)

    t1 = actual_strassen(a, matrix_subtraction(f, h))
    t2 = actual_strassen(matrix_addition(a, b), h)
    t3 = actual_strassen(matrix_addition(c, d), e)
    t4 = actual_strassen(d, matrix_subtraction(g, e))
    t5 = actual_strassen(matrix_addition(a, d), matrix_addition(e, h))
    t6 = actual_strassen(matrix_subtraction(b, d), matrix_addition(g, h))
    t7 = actual_strassen(matrix_subtraction(a, c), matrix_addition(e, f))

    top_left  = matrix_addition(matrix_subtraction(matrix_addition(t5, t4), t2), t6)
    top_right = matrix_addition(t1, t2)
    bot_left  = matrix_addition(t3, t4)
    bot_right = matrix_subtraction(matrix_subtraction(matrix_addition(t1, t5), t3), t7)

    new_matrix = []
    for i in range(len(top_right)):
        new_matrix.append(top_left[i] + top_right[i])
    for i in range(len(bot_right)):
        new_matrix.append(bot_left[i] + bot_right[i])
    return new_matrix


def strassen(matrix1: list, matrix2: list) -> list:
    if matrix_dimensions(matrix1)[1] != matrix_dimensions(matrix2)[0]:
        raise Exception("Incompatible dimensions")

    dim1 = matrix_dimensions(matrix1)
    dim2 = matrix_dimensions(matrix2)

    if dim1[0] == dim1[1] and dim2[0] == dim2[1]:
        return [matrix1, matrix2]

    maximum = max(*dim1, *dim2)
    maxim = int(math.pow(2, math.ceil(math.log2(maximum))))
    new_matrix1 = [row[:] for row in matrix1]
    new_matrix2 = [row[:] for row in matrix2]

    for i in range(maxim):
        if i < dim1[0]:
            new_matrix1[i].extend([0] * (maxim - dim1[1]))
        else:
            new_matrix1.append([0] * maxim)
        if i < dim2[0]:
            new_matrix2[i].extend([0] * (maxim - dim2[1]))
        else:
            new_matrix2.append([0] * maxim)

    final_matrix = actual_strassen(new_matrix1, new_matrix2)

    for i in range(maxim):
        if i < dim1[0]:
            final_matrix[i] = final_matrix[i][:dim2[1]]
    return final_matrix


if __name__ == "__main__":
    matrix1 = [
        [2, 3, 4, 5],
        [6, 4, 3, 1],
        [2, 3, 6, 7],
        [3, 1, 2, 4],
        [2, 3, 4, 5],
        [6, 4, 3, 1],
        [2, 3, 6, 7],
        [3, 1, 2, 4],
        [2, 3, 4, 5],
        [6, 2, 3, 1],
    ]
    matrix2 = [[0, 2, 1, 1], [16, 2, 3, 3], [2, 2, 7, 7], [13, 11, 22, 4]]
    print(strassen(matrix1, matrix2))
