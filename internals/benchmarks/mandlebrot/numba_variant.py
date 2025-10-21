from contextlib import closing
from itertools import islice
from os import cpu_count
from sys import argv, stdout
from numba import jit


@jit(nopython=True)
def compute_mandelbrot_row(y, n):
    c1 = 2.0 / n
    c0 = -1.5 + 1j * y * c1 - 1j
    result = []
    
    x = 0
    while x < n:
        pixel = 0
        c = x * c1 + c0
        
        for bit_pos in range(8):
            if x + bit_pos >= n:
                break
                
            z = c
            in_set = True
            
            for _ in range(49):
                z = z * z + c
                if abs(z) >= 2.0:
                    in_set = False
                    break
            
            if in_set:
                pixel |= (128 >> bit_pos)
            
            c += c1
        
        result.append(pixel)
        x += 8
    
    return result

def pixels(y, n, abs_func):
    return iter(compute_mandelbrot_row(y, n))

def compute_row(p):
    y, n = p
    result = bytearray(islice(pixels(y, n, abs), (n + 7) // 8))
    result[-1] &= 0xff << (8 - n % 8)
    return y, result

def ordered_rows(rows, n):
    order = [None] * n
    i = 0
    j = n
    while i < len(order):
        if j > 0:
            row = next(rows)
            order[row[0]] = row
            j -= 1

        if order[i]:
            yield order[i]
            order[i] = None
            i += 1

def compute_rows(n, f):
    row_jobs = ((y, n) for y in range(n))

    if cpu_count() < 2:
        yield from map(f, row_jobs)
    else:
        from multiprocessing import Pool
        with Pool() as pool:
            unordered_rows = pool.imap_unordered(f, row_jobs)
            yield from ordered_rows(unordered_rows, n)

def mandelbrot(n):
    write = stdout.buffer.write

    with closing(compute_rows(n, compute_row)) as rows:
        write("P4\n{0} {0}\n".format(n).encode())
        for row in rows:
            write(row[1])

if __name__ == '__main__':
    import time
    import io

    n = 1000

    start_time = time.time()
    print(f"Benchmark start: {start_time}")

    cold_start = time.time()
    old_stdout = stdout
    stdout = io.BytesIO()
    mandelbrot(n)
    stdout = old_stdout
    cold_end = time.time()
    cold_duration = cold_end - cold_start
    print(f"Cold start: {cold_start}")
    print(f"Cold end: {cold_end}")
    print(f"Cold duration: {cold_duration}")

    warm_start = time.time()
    old_stdout = stdout
    stdout = io.BytesIO()
    mandelbrot(n)
    stdout = old_stdout
    warm_end = time.time()
    warm_duration = warm_end - warm_start
    print(f"Warm start: {warm_start}")
    print(f"Warm end: {warm_end}")
    print(f"Warm duration: {warm_duration}")