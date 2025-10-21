# cython: language_level=3
import time
import multiprocessing as mp


ctypedef (object, object) TreeNode


cdef TreeNode make_tree(int d):
    if d > 0:
        d -= 1
        return (make_tree(d), make_tree(d))
    return (None, None)


cdef int check_tree(TreeNode node):
    cdef object l, r
    l, r = node
    if l is None:
        return 1
    else:
        return 1 + check_tree(l) + check_tree(r)


cdef int make_check(tuple itde):
    cdef int i, d
    i, d = itde
    return check_tree(make_tree(d))


def get_argchunks(int i, int d, int chunksize=5000):
    assert chunksize % 2 == 0
    chunk = []
    cdef int k
    for k in range(1, i + 1):
        chunk.extend([(k, d)])
        if len(chunk) == chunksize:
            yield chunk
            chunk = []
    if len(chunk) > 0:
        yield chunk


def run_benchmark(int n, int min_depth=4):
    cdef int max_depth = max(min_depth + 2, n)
    cdef int stretch_depth = max_depth + 1

    if mp.cpu_count() > 1:
        pool = mp.Pool()
        chunkmap = pool.map
    else:
        chunkmap = map

    make_check((0, stretch_depth))

    long_lived_tree = make_tree(max_depth)

    cdef int mmd = max_depth + min_depth
    cdef int d, i, cs
    for d in range(min_depth, stretch_depth, 2):
        i = 2 ** (mmd - d)
        cs = 0
        for argchunk in get_argchunks(i, d):
            cs += sum(chunkmap(make_check, argchunk))

    check_tree(long_lived_tree)


if __name__ == '__main__':
    n = 18

    run_benchmark(n)
    print(time.time())
    run_benchmark(n)