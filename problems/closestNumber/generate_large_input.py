import random

# File path where the generated input will be saved
output_file_path = "closestNumber/input/large_input.txt"

# Number of integers to generate (500 million)
N = 300_000_000

# Range for random integer generation
MIN_VALUE = -10**7
MAX_VALUE = 10**7

# Generate the file
with open(output_file_path, 'w') as f:
    # Write the number of integers (first line)
    f.write(f"{N}\n")
    
    # Generate and write the integers (second line)
    for i in range(N):
        # Write the random integer followed by a space (no newline until the end)
        f.write(f"{random.randint(MIN_VALUE, MAX_VALUE)} ")
    
    # Optionally, you could print a completion message
    print(f"Generated {N} random integers in {output_file_path}.")
