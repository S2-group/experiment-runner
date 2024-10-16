import random

# Path to save the large input file
output_file_path = "arrayManipulation/input/large_input.txt"

# Define large values for n and m
n = 500000000  # Size of the array (1 million)
m = 500000  # Number of queries (100 thousand)

# Define the range for random a, b, and k
MIN_VALUE = 1
MAX_VALUE = n
MIN_K = 1
MAX_K = 1000

# Generate the file
with open(output_file_path, 'w') as f:
    # Write the first line with n and m
    f.write(f"{n} {m}\n")
    
    # Generate m queries and write them to the file
    for _ in range(m):
        a = random.randint(MIN_VALUE, MAX_VALUE - 1)
        b = random.randint(a, MAX_VALUE)  # Ensure b >= a
        k = random.randint(MIN_K, MAX_K)
        f.write(f"{a} {b} {k}\n")

print(f"Generated large input file with n={n}, m={m} at {output_file_path}")
