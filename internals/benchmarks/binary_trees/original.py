import time
import multiprocessing as mp


def make_tree(d):

    if d > 0:
        d -= 1
        return (make_tree(d), make_tree(d))
    return (None, None)


def check_tree(node):

    (l, r) = node
    if l is None:
        return 1
    else:
        return 1 + check_tree(l) + check_tree(r)


def make_check(itde, make=make_tree, check=check_tree):

    i, d = itde
    return check(make(d))


def get_argchunks(i, d, chunksize=5000):

    assert chunksize % 2 == 0
    chunk = []
    for k in range(1, i + 1):
        chunk.extend([(k, d)])
        if len(chunk) == chunksize:
            yield chunk
            chunk = []
    if len(chunk) > 0:
        yield chunk


def run_benchmark(n, min_depth=4):

    max_depth = max(min_depth + 2, n)
    stretch_depth = max_depth + 1
    if mp.cpu_count() > 1:
        pool = mp.Pool()
        chunkmap = pool.map
    else:
        chunkmap = map

    make_check((0, stretch_depth))

    long_lived_tree = make_tree(max_depth)

    mmd = max_depth + min_depth
    for d in range(min_depth, stretch_depth, 2):
        i = 2 ** (mmd - d)
        cs = 0
        for argchunk in get_argchunks(i,d):
            cs += sum(chunkmap(make_check, argchunk))

    check_tree(long_lived_tree)


n = 18

run_benchmark(n)
print(time.time())
run_benchmark(n)