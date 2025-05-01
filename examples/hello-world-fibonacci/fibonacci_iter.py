# Implementation by Mandy Wong (https://realpython.com/fibonacci-sequence-python/)
import sys

def fib(n):
	a, b = 0, 1
	for i in range(0, n):
		a, b = b, a + b
	return a

for n in range(int(sys.argv[1])):
	print(fib(n))
