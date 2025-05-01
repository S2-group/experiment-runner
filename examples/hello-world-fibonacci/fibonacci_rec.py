# Implementation by Mandy Wong (https://realpython.com/fibonacci-sequence-python/)
import sys

def fib(n):
	if n in {0, 1}:  # Base case
		return n
	return fib(n - 1) + fib(n - 2)  # Recursive case

for n in range(int(sys.argv[1])):
	print(fib(n))
