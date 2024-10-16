import random

n = 130000000  
m = 130000000  

with open('../input/array_manipulation.txt', 'w') as f:
    f.write(f"{n} {m}\n")
    for _ in range(m):
        a = random.randint(1, n // 2)  
        b = random.randint(n // 2, n)  
        k = random.randint(1, 1000)     
        f.write(f"{a} {b} {k}\n")
