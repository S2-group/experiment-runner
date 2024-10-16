#!/bin/python3

import os


# Complete the 'arrayManipulation' function below.
#
# The function is expected to return a LONG_INTEGER.
# The function accepts following parameters:
#  1. INTEGER n
#  2. 2D_INTEGER_ARRAY queries
#

def arrayManipulation(n, queries):
    # Dictionary to store the difference array
    Is = {}
    for x in queries:
        a, b, k = x
        if k == 0:
            continue
        Is[a] = Is.get(a, 0) + k
        Is[b + 1] = Is.get(b + 1, 0) - k
        
    # Finding the maximum value after applying the operations
    x, v = 0, 0
    for i in sorted(Is):
        v += Is[i]
        if v > x:
            x = v

    return x

if __name__ == '__main__':
    # Path to the input file
    input_file_path = "arrayManipulation/input/large_input.txt"  # Update with your own file path
    
    # Read the input file
    with open(input_file_path, 'r') as file:
        # First line contains n and m
        first_line = file.readline().strip().split()
        n = int(first_line[0])
        m = int(first_line[1])
        
        # Subsequent lines contain the queries
        queries = []
        for _ in range(m):
            queries.append(list(map(int, file.readline().strip().split())))

    # Call the function to perform the array manipulation
    result = arrayManipulation(n, queries)
    
    # Write the result to the output file
    output_file_path = "arrayManipulation/output/output.txt"  # Path to the output file
    with open(output_file_path, 'w') as fptr:
        fptr.write(str(result) + '\n')
        fptr.close()
