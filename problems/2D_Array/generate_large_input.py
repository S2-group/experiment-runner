import random

# Path to save the large input file
output_file_path = "2D_Array/input/large_input.txt"

# Define the grid size (e.g., 1000x1000 or larger to take time)
rows = 1000000
cols = 1000000

# Define the range for random integers in the grid
MIN_VALUE = -9
MAX_VALUE = 9

# Generate the file
with open(output_file_path, 'w') as f:
    for _ in range(rows):
        # Generate a row of random integers
        row = ' '.join(str(random.randint(MIN_VALUE, MAX_VALUE)) for _ in range(cols))
        f.write(row + '\n')

print(f"Generated {rows}x{cols} grid in {output_file_path}.")
