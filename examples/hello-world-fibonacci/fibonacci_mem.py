# Implementation by Mandy Wong (https://realpython.com/fibonacci-sequence-python/)
import sys

cache = {0: 0, 1: 1}

def fib(n):
	if n in cache:  # Base case
		return cache[n]
	# Compute and cache the Fibonacci number
	cache[n] = fib(n - 1) + fib(n - 2)  # Recursive case
	return cache[n]

for n in range(int(sys.argv[1])):
	print(fib(n))
