#!/bin/python3

import os

# Complete the 'hourglassSum' function below.
#
# The function is expected to return an INTEGER.
# The function accepts 2D_INTEGER_ARRAY arr as parameter.
#

def hourglassSum(board):
    max_sum = float('-inf')  # To ensure we can handle negative hourglass sums
    
    # Initialize the first hourglass sum
    i, j = 0, 0
    m = sum([board[i][j], board[i][j+1], board[i][j+2], board[i+1][j+1], board[i+2][j], board[i+2][j+1], board[i+2][j+2]])
    
    # Loop through possible hourglasses in the 6x6 grid
    for i in range(4):
        for j in range(4):
            acc = sum([board[i][j], board[i][j+1], board[i][j+2],
                       board[i+1][j+1],
                       board[i+2][j], board[i+2][j+1], board[i+2][j+2]])
            m = max(m, acc)  # Update maximum sum
    
    return m

if __name__ == '__main__':
    input_file_path = "2D_Array/input/input.txt"  # input file path
    output_file_path = "2D_Array/output/output.txt"  # Path for the output file

    # Read the input file
    board = []
    with open(input_file_path, 'r') as file:
        for line in file:
            board.append(list(map(int, line.strip().split())))

    # Call the hourglassSum function to get the result
    result = hourglassSum(board)

    # Write the result to the output file
    with open(output_file_path, 'w') as fptr:
        fptr.write(str(result) + '\n')
        fptr.close()
