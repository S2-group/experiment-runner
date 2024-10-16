import random

n = 22500

with open('../input/2d_array.txt', 'w') as f:
    for _ in range(n):
        row = ' '.join(map(str, [random.randint(-9, 9) for _ in range(n)]))
        f.write(row + '\n')
