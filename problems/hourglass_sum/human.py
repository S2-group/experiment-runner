#!/bin/python3

import os

# Complete the 'hourglassSum' function below.
# The function is expected to return an INTEGER.
# The function accepts 2D_INTEGER_ARRAY arr as parameter.

def hourglassSum(board):
    # Initialize the maximum hourglass sum with a very low value
    max_sum = float('-inf')  # To ensure we can handle negative hourglass sums
    
    # Determine the number of rows and columns dynamically
    num_rows = len(board)
    num_cols = len(board[0])
    
    # Loop through all possible hourglass positions
    for i in range(num_rows - 2):  # Hourglass can only start in rows 0 to num_rows-3
        for j in range(num_cols - 2):  # Hourglass can only start in cols 0 to num_cols-3
            # Calculate the sum of the hourglass
            hourglass_sum = (
                board[i][j] + board[i][j+1] + board[i][j+2] +  # Top row of the hourglass
                board[i+1][j+1] +  # Middle of the hourglass
                board[i+2][j] + board[i+2][j+1] + board[i+2][j+2]  # Bottom row of the hourglass
            )
            # Update the maximum hourglass sum found so far
            max_sum = max(max_sum, hourglass_sum)
    
    return max_sum

if __name__ == '__main__':
    input_file_path = "2D_Array/input/large_input.txt"  # input file path
    output_file_path = "2D_Array/output/large_output.txt"  # Path for the output file

    # Read the input file and construct the matrix
    board = []
    with open(input_file_path, 'r') as file:
        for line in file:
            board.append(list(map(int, line.strip().split())))

    # Call the hourglassSum function to get the result
    result = hourglassSum(board)

    # Write the result to the output file
    with open(output_file_path, 'w') as fptr:
        fptr.write(str(result) + '\n')
